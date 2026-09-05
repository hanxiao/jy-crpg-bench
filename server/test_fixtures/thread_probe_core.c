/* Minimal libretro fixture: keep retro_run active until the test releases it. */
#include "libretro.h"
#include <stdatomic.h>
#include <string.h>
#include <time.h>

static retro_environment_t environment;
static retro_video_refresh_t video;
static atomic_int running, release_run, overlaps, fail_serialize, state_size;
static atomic_int game_loaded, unloads, premature_deinit;
static void touch_core(void) {
    if (atomic_load(&running)) atomic_fetch_add(&overlaps, 1);
}
static void keyboard(bool down, unsigned key, uint32_t character, uint16_t mods) {
    (void)down; (void)key; (void)character; (void)mods;
    touch_core();
}
void probe_reset(void) {
    atomic_store(&running, 0); atomic_store(&release_run, 0);
    atomic_store(&overlaps, 0); atomic_store(&fail_serialize, 0);
    atomic_store(&state_size, 16);
    atomic_store(&game_loaded, 0); atomic_store(&unloads, 0);
    atomic_store(&premature_deinit, 0);
}
int probe_running(void) { return atomic_load(&running); }
int probe_overlaps(void) { return atomic_load(&overlaps); }
void probe_release(void) { atomic_store(&release_run, 1); }
void probe_fail_serialize(int value) { atomic_store(&fail_serialize, value); }
void probe_state_size(int value) { atomic_store(&state_size, value); }
int probe_unloads(void) { return atomic_load(&unloads); }
int probe_premature_deinit(void) { return atomic_load(&premature_deinit); }
void retro_set_environment(retro_environment_t cb) { environment = cb; }
void retro_set_video_refresh(retro_video_refresh_t cb) { video = cb; }
void retro_set_audio_sample(retro_audio_sample_t cb) { (void)cb; }
void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { (void)cb; }
void retro_set_input_poll(retro_input_poll_t cb) { (void)cb; }
void retro_set_input_state(retro_input_state_t cb) { (void)cb; }
void retro_set_controller_port_device(unsigned port, unsigned device) { (void)port; (void)device; }
void retro_init(void) {
    struct retro_keyboard_callback cb = { keyboard };
    environment(RETRO_ENVIRONMENT_SET_KEYBOARD_CALLBACK, &cb);
}
void retro_deinit(void) {
    touch_core();
    if (atomic_load(&game_loaded)) atomic_fetch_add(&premature_deinit, 1);
}
bool retro_load_game(const struct retro_game_info *info) {
    (void)info; atomic_store(&game_loaded, 1); return true;
}
void retro_unload_game(void) {
    touch_core(); atomic_store(&game_loaded, 0); atomic_fetch_add(&unloads, 1);
}
void retro_get_system_av_info(struct retro_system_av_info *av) {
    memset(av, 0, sizeof(*av));
    av->timing.fps = 60; av->timing.sample_rate = 48000;
}
void retro_run(void) {
    atomic_store(&running, 1);
    while (!atomic_load(&release_run)) {
        struct timespec delay = { 0, 1000000 };
        nanosleep(&delay, NULL);
    }
    uint32_t pixel = 0x00123456;
    video(&pixel, 1, 1, sizeof(pixel));
    atomic_store(&running, 0);
}
void retro_reset(void) { touch_core(); }
size_t retro_serialize_size(void) { touch_core(); return (size_t)atomic_load(&state_size); }
bool retro_serialize(void *data, size_t size) {
    touch_core();
    if (size < 16 || atomic_load(&fail_serialize)) return false;
    memset(data, 0, size);
    ((unsigned char *)data)[0] = 123;
    return true;
}
bool retro_unserialize(const void *data, size_t size) {
    (void)data; touch_core(); return size == 16;
}
size_t retro_get_memory_size(unsigned id) { (void)id; touch_core(); return 16; }
void *retro_get_memory_data(unsigned id) {
    static unsigned char memory[16] = { 42 };
    (void)id; touch_core(); return memory;
}
