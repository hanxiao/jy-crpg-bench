#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*core_log_fn)(const char *line);

/* Pin a libretro core option. Must be called before core_init. */
void core_set_option(const char *key, const char *value);
const char *core_get_option(const char *key);

/* One initialization per process: a second call over a live core fails.
   Re-initializing after core_shutdown() is not guaranteed by the libretro
   contract; for a fresh origin, start a new process. */
bool core_init(const char *core_path, const char *game_path, const char *save_dir);
void core_shutdown(void);
void core_run_frame(void);
void core_reset(void);

/* Keyboard: retrok is a RETROK_* value. Routed to the core's keyboard callback. */
void core_key(int retrok, bool down);
/* CLOCK_MONOTONIC absolute seconds; zero disables the key-down deadline. */
bool core_key_before_deadline(int retrok, bool down, double deadline);
void core_release_all_keys(void);

/* Mouse: relative motion in core pixels, buttons 0=left 1=right 2=middle. */
void core_mouse_move(int dx, int dy);
void core_mouse_button(int button, bool down);

bool core_save_state(const char *path);
bool core_load_state(const char *path);

int core_width(void);
int core_height(void);
int core_pitch(void);
const void *core_pixels(void);
/* Distinct video frames the core has produced. Stalls while the picture is
   unchanged, because the core skips duplicate frames. */
uint64_t core_frame_serial(void);
/* Emulated frames run. Always advances while the emulator is alive. */
uint64_t core_ticks(void);
uint64_t core_frame_hash(void);

double core_fps(void);
double core_sample_rate(void);
double core_aspect(void);

/* Drain emulated audio. Returns frames written (stereo interleaved int16). */
size_t core_audio_read(int16_t *dst, size_t frames);
size_t core_audio_available(void);
void core_audio_reset(void);

void core_lock(void);
void core_unlock(void);
void core_set_log(core_log_fn fn);
const char *core_last_error(void);

#ifdef __cplusplus
}
#endif
