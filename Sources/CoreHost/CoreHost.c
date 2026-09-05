#include "CoreHost.h"

#include <dlfcn.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libretro.h"

typedef void (*fn_void)(void);
typedef bool (*fn_load)(const struct retro_game_info *);
typedef size_t (*fn_serialize_size)(void);
typedef bool (*fn_serialize)(void *, size_t);
typedef bool (*fn_unserialize)(const void *, size_t);
typedef void (*fn_get_av)(struct retro_system_av_info *);
typedef void *(*fn_mem_data)(unsigned);
typedef size_t (*fn_mem_size)(unsigned);
typedef void (*fn_set_env)(retro_environment_t);
typedef void (*fn_set_video)(retro_video_refresh_t);
typedef void (*fn_set_audio)(retro_audio_sample_t);
typedef void (*fn_set_audio_batch)(retro_audio_sample_batch_t);
typedef void (*fn_set_poll)(retro_input_poll_t);
typedef void (*fn_set_input)(retro_input_state_t);
typedef void (*fn_set_controller)(unsigned, unsigned);

static void *g_lib;
static fn_void g_init, g_deinit, g_run, g_reset;
static fn_load g_load;
static fn_serialize_size g_ser_size;
static fn_serialize g_ser;
static fn_unserialize g_unser;
static fn_get_av g_av;
/* The emulated machine's own memory, if the core will hand it over. Reading a
   couple of shorts out of it costs nothing, where serialising the whole
   machine to find the same shorts costs megabytes per action. */
static fn_mem_data g_mem_data;
static fn_mem_size g_mem_size;
static fn_set_controller g_set_controller;

/* Libretro entry points are not reentrant. The HTTP thread reads state while
   the emulation thread calls retro_run; serializing concurrently can leave
   DOSBox Pure's frame/pause handshake stuck. Keep core operations separate
   from the framebuffer mutex: retro_run itself invokes video_cb, which takes
   g_mu. Callbacks must not try to acquire this execution mutex. */
static pthread_mutex_t g_exec_mu = PTHREAD_MUTEX_INITIALIZER;

/* ---- video ---- */
static pthread_mutex_t g_mu = PTHREAD_MUTEX_INITIALIZER;
static uint8_t *g_fb;
static size_t g_fb_cap;
static int g_w, g_h, g_pitch;
static _Atomic uint64_t g_serial;
static _Atomic uint64_t g_ticks;
static _Atomic uint64_t g_hash;

/* ---- audio ring ---- */
#define AUDIO_RING_FRAMES 32768
static pthread_mutex_t g_amu = PTHREAD_MUTEX_INITIALIZER;
static int16_t g_ring[AUDIO_RING_FRAMES * 2];
static size_t g_ring_r, g_ring_w;

/* ---- input ---- */
static retro_keyboard_event_t g_kbd_cb;
static uint8_t g_keys[RETROK_LAST];
static int g_mouse_dx, g_mouse_dy;
static uint8_t g_mouse_btn[3];

/* ---- misc ---- */
static char g_err[512];
static char g_save_dir[1024];
static char g_sys_dir[1024];
static core_log_fn g_log;
static double g_fps = 60.0, g_rate = 48000.0, g_aspect = 4.0 / 3.0;

static void slog(const char *s) {
    if (g_log) g_log(s);
    else fprintf(stderr, "%s\n", s);
}

static void slogf(const char *fmt, ...) {
    char buf[1024];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    size_t n = strlen(buf);
    while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r')) buf[--n] = 0;
    slog(buf);
}

static void set_err(const char *s) {
    snprintf(g_err, sizeof(g_err), "%s", s);
    slog(s);
}

static void RETRO_CALLCONV retro_log_cb(enum retro_log_level level, const char *fmt, ...) {
    if (level < RETRO_LOG_WARN) return;
    char buf[1024];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    size_t n = strlen(buf);
    while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r')) buf[--n] = 0;
    if (n) slogf("[core] %s", buf);
}

/* Core options we pin. Anything not listed falls through to the core default. */
#define MAX_VARS 64
struct kv { char k[64], v[64]; };
static struct kv g_vars[MAX_VARS] = {
    { "dosbox_pure_conf",             "false"  },
    { "dosbox_pure_menu_time",        "99"     },
    { "dosbox_pure_machine",          "svga"   },
    { "dosbox_pure_memory_size",      "16"     },
    /* Pentium-100 budget. Measured on M3 Ultra: holds a full 70.09 fps at ~31%
       of one core and boots to the title in 15.9s - same as "max", which costs
       99%. "auto" ramps up from cold and boots 3.6s slower. */
    { "dosbox_pure_cycles",           "77000"  },
    { "dosbox_pure_cpu_core",         "auto"   },
    { "dosbox_pure_force60fps",       "false"  },
    { "dosbox_pure_perfstats",        "none"   },
    { "dosbox_pure_savestate",        "on"     },
    { "dosbox_pure_audiorate",        "48000"  },
    { "dosbox_pure_sblaster_conf",    "A220 I7 D1 H5" },
    { "dosbox_pure_midi",             "disabled" },
    { "dosbox_pure_bind_unused",      "false"  },
    { "dosbox_pure_on_screen_keyboard", "false" },
    { "dosbox_pure_auto_mapping",     "false"  },
    { "dosbox_pure_mouse_input",      "true"   },
    { "dosbox_pure_aspect_correction", "false" },
};
static size_t g_var_count = 0;

void core_set_option(const char *key, const char *value) {
    if (!key || !value) return;
    if (g_var_count == 0) {
        while (g_var_count < MAX_VARS && g_vars[g_var_count].k[0]) g_var_count++;
    }
    for (size_t i = 0; i < g_var_count; i++) {
        if (strcmp(g_vars[i].k, key) == 0) {
            snprintf(g_vars[i].v, sizeof(g_vars[i].v), "%s", value);
            return;
        }
    }
    if (g_var_count >= MAX_VARS) return;
    snprintf(g_vars[g_var_count].k, sizeof(g_vars[g_var_count].k), "%s", key);
    snprintf(g_vars[g_var_count].v, sizeof(g_vars[g_var_count].v), "%s", value);
    g_var_count++;
}

const char *core_get_option(const char *key) {
    for (size_t i = 0; i < MAX_VARS && g_vars[i].k[0]; i++)
        if (strcmp(g_vars[i].k, key) == 0) return g_vars[i].v;
    return "";
}

static bool env_cb(unsigned cmd, void *data) {
    switch (cmd & 0xFFFF) {
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: {
        struct retro_log_callback *cb = data;
        cb->log = retro_log_cb;
        return true;
    }
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
        /* We only render XRGB8888. */
        return *(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_XRGB8888;
    }
    case RETRO_ENVIRONMENT_SET_KEYBOARD_CALLBACK: {
        const struct retro_keyboard_callback *cb = data;
        g_kbd_cb = cb ? cb->callback : NULL;
        return true;
    }
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        *(bool *)data = true;
        return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        *(const char **)data = g_sys_dir;
        return true;
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
        *(const char **)data = g_save_dir;
        return true;
    case RETRO_ENVIRONMENT_GET_INPUT_DEVICE_CAPABILITIES:
        *(uint64_t *)data = (1 << RETRO_DEVICE_JOYPAD) | (1 << RETRO_DEVICE_KEYBOARD) | (1 << RETRO_DEVICE_MOUSE);
        return true;
    case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO:
    case RETRO_ENVIRONMENT_SET_GEOMETRY: {
        const struct retro_system_av_info *av = data;
        if (cmd == RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO) {
            if (av->timing.fps > 1) g_fps = av->timing.fps;
            if (av->timing.sample_rate > 1) g_rate = av->timing.sample_rate;
        }
        if (av->geometry.aspect_ratio > 0.01) g_aspect = av->geometry.aspect_ratio;
        return true;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *var = data;
        if (!var || !var->key) return false;
        for (size_t i = 0; i < MAX_VARS && g_vars[i].k[0]; i++) {
            if (strcmp(var->key, g_vars[i].k) == 0) {
                var->value = g_vars[i].v;
                return true;
            }
        }
        var->value = NULL;
        return false;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        *(bool *)data = false;
        return true;
    case RETRO_ENVIRONMENT_SET_MESSAGE: {
        const struct retro_message *m = data;
        if (m && m->msg) slogf("[core] %s", m->msg);
        return true;
    }
    case RETRO_ENVIRONMENT_SET_MESSAGE_EXT: {
        const struct retro_message_ext *m = data;
        if (m && m->msg) slogf("[core] %s", m->msg);
        return true;
    }
    case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE:
        *(int *)data = 0x3; /* video + audio enabled */
        return true;
    case RETRO_ENVIRONMENT_GET_FASTFORWARDING:
        *(bool *)data = false;
        return true;
    case RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_DISPLAY:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_UPDATE_DISPLAY_CALLBACK:
    case RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE:
    case RETRO_ENVIRONMENT_SET_DISK_CONTROL_EXT_INTERFACE:
        return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        *(unsigned *)data = 0; /* keep the core on the legacy GET_VARIABLE path */
        return true;
    default:
        return false;
    }
}

static void video_cb(const void *data, unsigned width, unsigned height, size_t pitch) {
    if (!data || data == RETRO_HW_FRAME_BUFFER_VALID) return;
    pthread_mutex_lock(&g_mu);
    size_t need = (size_t)height * pitch;
    if (need > g_fb_cap) {
        uint8_t *nb = realloc(g_fb, need);
        if (nb) { g_fb = nb; g_fb_cap = need; }
    }
    if (g_fb && need <= g_fb_cap) {
        memcpy(g_fb, data, need);
        g_w = (int)width;
        g_h = (int)height;
        g_pitch = (int)pitch;
        /* FNV-1a over a sparse sample of the frame: cheap change detection. */
        uint64_t h = 1469598103934665603ULL;
        const uint8_t *p = g_fb;
        size_t step = need > 4096 ? need / 4096 : 1;
        for (size_t i = 0; i < need; i += step) {
            h ^= p[i];
            h *= 1099511628211ULL;
        }
        g_hash = h;
        g_serial++;
    }
    pthread_mutex_unlock(&g_mu);
}

static void push_audio(const int16_t *data, size_t frames) {
    pthread_mutex_lock(&g_amu);
    for (size_t i = 0; i < frames; i++) {
        size_t next = (g_ring_w + 1) % AUDIO_RING_FRAMES;
        if (next == g_ring_r) break; /* full: drop rest */
        g_ring[g_ring_w * 2] = data[i * 2];
        g_ring[g_ring_w * 2 + 1] = data[i * 2 + 1];
        g_ring_w = next;
    }
    pthread_mutex_unlock(&g_amu);
}

static void audio_cb(int16_t left, int16_t right) {
    int16_t f[2] = { left, right };
    push_audio(f, 1);
}

static size_t audio_batch_cb(const int16_t *data, size_t frames) {
    push_audio(data, frames);
    return frames;
}

size_t core_audio_read(int16_t *dst, size_t frames) {
    pthread_mutex_lock(&g_amu);
    size_t n = 0;
    while (n < frames && g_ring_r != g_ring_w) {
        dst[n * 2] = g_ring[g_ring_r * 2];
        dst[n * 2 + 1] = g_ring[g_ring_r * 2 + 1];
        g_ring_r = (g_ring_r + 1) % AUDIO_RING_FRAMES;
        n++;
    }
    pthread_mutex_unlock(&g_amu);
    return n;
}

size_t core_audio_available(void) {
    pthread_mutex_lock(&g_amu);
    size_t n = (g_ring_w + AUDIO_RING_FRAMES - g_ring_r) % AUDIO_RING_FRAMES;
    pthread_mutex_unlock(&g_amu);
    return n;
}

void core_audio_reset(void) {
    pthread_mutex_lock(&g_amu);
    g_ring_r = g_ring_w = 0;
    pthread_mutex_unlock(&g_amu);
}

static void poll_cb(void) {}

static int16_t input_cb(unsigned port, unsigned device, unsigned index, unsigned id) {
    (void)index;
    if (port != 0) return 0;
    switch (device) {
    case RETRO_DEVICE_KEYBOARD:
        return (id < RETROK_LAST && g_keys[id]) ? 1 : 0;
    case RETRO_DEVICE_MOUSE:
        switch (id) {
        case RETRO_DEVICE_ID_MOUSE_X: { int v = g_mouse_dx; g_mouse_dx = 0; return (int16_t)v; }
        case RETRO_DEVICE_ID_MOUSE_Y: { int v = g_mouse_dy; g_mouse_dy = 0; return (int16_t)v; }
        case RETRO_DEVICE_ID_MOUSE_LEFT:   return g_mouse_btn[0];
        case RETRO_DEVICE_ID_MOUSE_RIGHT:  return g_mouse_btn[1];
        case RETRO_DEVICE_ID_MOUSE_MIDDLE: return g_mouse_btn[2];
        default: return 0;
        }
    default:
        return 0;
    }
}

static void *sym(const char *name, bool required) {
    void *p = dlsym(g_lib, name);
    if (!p && required) {
        char buf[256];
        snprintf(buf, sizeof(buf), "missing symbol %s", name);
        set_err(buf);
    }
    return p;
}

bool core_init(const char *core_path, const char *game_path, const char *save_dir) {
    g_err[0] = 0;
    snprintf(g_save_dir, sizeof(g_save_dir), "%s", save_dir ? save_dir : ".");
    snprintf(g_sys_dir, sizeof(g_sys_dir), "%s", save_dir ? save_dir : ".");

    g_lib = dlopen(core_path, RTLD_NOW | RTLD_LOCAL);
    if (!g_lib) {
        set_err(dlerror());
        return false;
    }

    fn_set_env set_env = sym("retro_set_environment", true);
    fn_set_video set_video = sym("retro_set_video_refresh", true);
    fn_set_audio set_audio = sym("retro_set_audio_sample", true);
    fn_set_audio_batch set_audio_batch = sym("retro_set_audio_sample_batch", true);
    fn_set_poll set_poll = sym("retro_set_input_poll", true);
    fn_set_input set_input = sym("retro_set_input_state", true);
    g_init = (fn_void)sym("retro_init", true);
    g_deinit = (fn_void)sym("retro_deinit", false);
    g_run = (fn_void)sym("retro_run", true);
    g_reset = (fn_void)sym("retro_reset", false);
    g_load = (fn_load)sym("retro_load_game", true);
    g_ser_size = (fn_serialize_size)sym("retro_serialize_size", false);
    g_ser = (fn_serialize)sym("retro_serialize", false);
    g_unser = (fn_unserialize)sym("retro_unserialize", false);
    g_av = (fn_get_av)sym("retro_get_system_av_info", false);
    g_mem_data = (fn_mem_data)sym("retro_get_memory_data", false);
    g_mem_size = (fn_mem_size)sym("retro_get_memory_size", false);
    g_set_controller = (fn_set_controller)sym("retro_set_controller_port_device", false);
    if (!set_env || !g_init || !g_load || !g_run) return false;

    set_env(env_cb);
    set_video(video_cb);
    set_audio(audio_cb);
    set_audio_batch(audio_batch_cb);
    set_poll(poll_cb);
    set_input(input_cb);
    g_init();

    struct retro_game_info info;
    memset(&info, 0, sizeof(info));
    info.path = game_path;
    if (!g_load(&info)) {
        set_err("retro_load_game failed");
        return false;
    }

    if (g_set_controller) g_set_controller(0, RETRO_DEVICE_KEYBOARD);

    if (g_av) {
        struct retro_system_av_info av;
        memset(&av, 0, sizeof(av));
        g_av(&av);
        if (av.timing.fps > 1) g_fps = av.timing.fps;
        if (av.timing.sample_rate > 1) g_rate = av.timing.sample_rate;
        if (av.geometry.aspect_ratio > 0.01) g_aspect = av.geometry.aspect_ratio;
    }
    slogf("core loaded  fps=%.3f rate=%.0f aspect=%.3f", g_fps, g_rate, g_aspect);
    return true;
}

void core_shutdown(void) {
    pthread_mutex_lock(&g_exec_mu);
    if (g_deinit) g_deinit();
    g_run = g_deinit = g_reset = NULL;
    g_ser = NULL; g_unser = NULL; g_ser_size = NULL;
    g_mem_data = NULL; g_mem_size = NULL; g_kbd_cb = NULL;
    g_lib = NULL; /* leave dlclose out: the core spawns threads that outlive deinit */
    pthread_mutex_lock(&g_mu);
    free(g_fb);
    g_fb = NULL;
    g_fb_cap = 0;
    g_w = g_h = g_pitch = 0;
    pthread_mutex_unlock(&g_mu);
    pthread_mutex_unlock(&g_exec_mu);
}

void core_run_frame(void) {
    pthread_mutex_lock(&g_exec_mu);
    if (g_run) g_run();
    g_ticks++;
    pthread_mutex_unlock(&g_exec_mu);
}

static void release_all_keys_unlocked(void);

void core_reset(void) {
    pthread_mutex_lock(&g_exec_mu);
    release_all_keys_unlocked();
    core_audio_reset();
    if (g_reset) g_reset();
    pthread_mutex_unlock(&g_exec_mu);
}

void core_key(int retrok, bool down) {
    if (retrok < 0 || retrok >= (int)RETROK_LAST) return;
    pthread_mutex_lock(&g_exec_mu);
    if (g_keys[retrok] != (down ? 1 : 0)) {
        g_keys[retrok] = down ? 1 : 0;
        if (g_kbd_cb) g_kbd_cb(down, (unsigned)retrok, 0, 0);
    }
    pthread_mutex_unlock(&g_exec_mu);
}

static void release_all_keys_unlocked(void) {
    for (int i = 0; i < (int)RETROK_LAST; i++) {
        if (g_keys[i]) {
            g_keys[i] = 0;
            if (g_kbd_cb) g_kbd_cb(false, (unsigned)i, 0, 0);
        }
    }
}

void core_release_all_keys(void) {
    pthread_mutex_lock(&g_exec_mu);
    release_all_keys_unlocked();
    pthread_mutex_unlock(&g_exec_mu);
}

void core_mouse_move(int dx, int dy) {
    pthread_mutex_lock(&g_exec_mu);
    g_mouse_dx += dx;
    g_mouse_dy += dy;
    pthread_mutex_unlock(&g_exec_mu);
}

void core_mouse_button(int button, bool down) {
    pthread_mutex_lock(&g_exec_mu);
    if (button >= 0 && button < 3) g_mouse_btn[button] = down ? 1 : 0;
    pthread_mutex_unlock(&g_exec_mu);
}

/* DOSBox Pure exposes no memory regions - every retro_get_memory_size is 0 -
   so the only way to see the game's own variables is to serialise the machine
   and read them out of that. The buffer is kept and reused so this costs one
   serialise and a couple of loads per call, with no allocation and no file. */
static unsigned char *g_peek;
static size_t g_peek_cap;

int core_state_peek(const size_t *offs, int n, int16_t *out) {
    int result = -1;
    pthread_mutex_lock(&g_exec_mu);
    if (!g_ser || !g_ser_size) goto done;
    size_t need = g_ser_size();
    if (need == 0) goto done;
    if (need > g_peek_cap) {
        unsigned char *p = (unsigned char *)realloc(g_peek, need);
        if (!p) goto done;
        g_peek = p; g_peek_cap = need;
    }
    if (!g_ser(g_peek, need)) goto done;
    for (int i = 0; i < n; i++) {
        if (offs[i] + 2 > need) goto done;
        int16_t v;
        memcpy(&v, g_peek + offs[i], 2);
        out[i] = v;
    }
    result = 0;
done:
    pthread_mutex_unlock(&g_exec_mu);
    return result;
}

/* The whole machine as bytes, for the caller to search. Calibration used to
   write a scratch file next to the start state, which fails wherever that
   directory is not writable - which is what it is in the container. */
size_t core_state_size(void) {
    pthread_mutex_lock(&g_exec_mu);
    size_t n = g_ser_size ? g_ser_size() : 0;
    pthread_mutex_unlock(&g_exec_mu);
    return n;
}

int core_state_copy(unsigned char *dst, size_t cap) {
    int result = -1;
    pthread_mutex_lock(&g_exec_mu);
    if (g_ser && g_ser_size) {
        size_t need = g_ser_size();
        if (need && need <= cap) result = g_ser(dst, need) ? (int)need : -1;
    }
    pthread_mutex_unlock(&g_exec_mu);
    return result;
}

/* id is a RETRO_MEMORY_* constant: 0 system RAM, 1 save RAM, 2 RTC, 3 VRAM. */
size_t core_mem_size(unsigned id) {
    pthread_mutex_lock(&g_exec_mu);
    size_t n = g_mem_size ? g_mem_size(id) : 0;
    pthread_mutex_unlock(&g_exec_mu);
    return n;
}

bool core_mem_read(unsigned id, size_t off, void *dst, size_t n) {
    bool ok = false;
    pthread_mutex_lock(&g_exec_mu);
    if (g_mem_data && g_mem_size) {
        size_t sz = g_mem_size(id);
        unsigned char *p = (unsigned char *)g_mem_data(id);
        if (p && off + n <= sz) { memcpy(dst, p + off, n); ok = true; }
    }
    pthread_mutex_unlock(&g_exec_mu);
    return ok;
}

bool core_save_state(const char *path) {
    void *buf = NULL;
    size_t n = 0;
    bool ok = false;
    pthread_mutex_lock(&g_exec_mu);
    if (g_ser_size && g_ser) {
        n = g_ser_size();
        if (n && (buf = malloc(n))) ok = g_ser(buf, n);
    }
    pthread_mutex_unlock(&g_exec_mu);
    if (ok) {
        FILE *f = fopen(path, "wb");
        if (!f) { free(buf); set_err("cannot open savestate for write"); return false; }
        ok = fwrite(buf, 1, n, f) == n;
        fclose(f);
    } else {
        set_err("retro_serialize failed");
    }
    free(buf);
    return ok;
}

bool core_load_state(const char *path) {
    if (!g_unser) return false;
    FILE *f = fopen(path, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (n <= 0) { fclose(f); return false; }
    void *buf = malloc((size_t)n);
    if (!buf) { fclose(f); return false; }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n) { free(buf); return false; }
    pthread_mutex_lock(&g_exec_mu);
    release_all_keys_unlocked();
    bool ok = g_unser(buf, (size_t)n);
    if (ok) core_audio_reset();
    pthread_mutex_unlock(&g_exec_mu);
    free(buf);
    if (!ok) set_err("retro_unserialize failed");
    return ok;
}

int core_width(void) { return g_w; }
int core_height(void) { return g_h; }
int core_pitch(void) { return g_pitch; }
const void *core_pixels(void) { return g_fb; }
uint64_t core_frame_serial(void) { return g_serial; }
uint64_t core_ticks(void) { return g_ticks; }
uint64_t core_frame_hash(void) { return g_hash; }
double core_fps(void) { return g_fps; }
double core_sample_rate(void) { return g_rate; }
double core_aspect(void) { return g_aspect; }

void core_lock(void) { pthread_mutex_lock(&g_mu); }
void core_unlock(void) { pthread_mutex_unlock(&g_mu); }

void core_set_log(core_log_fn fn) { g_log = fn; }
const char *core_last_error(void) { return g_err; }
