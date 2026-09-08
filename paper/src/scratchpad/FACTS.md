### headline
sessions_ok 19 labels 14
### per label (CSV)
label|runs|total_actions|qmin|qmax|qmean|map_max|exit_secs_first|scene_max|lvl_max|exp_max|exit_rate_measures
Qwen3.8-27B-NVFP4|1|48|0.854|0.854|0.854|0||1|1|0|0
claude-fable-5|1|159|0.748|0.748|0.748|0||1|1|0|0
claude-fable-5-1|3|398|0.545|0.727|0.641|1|291.8|4|1|0|2
claude-opus-5|1|114|0.842|0.842|0.842|0||1|1|0|0
claude-sonnet-5|1|51|0.824|0.824|0.824|0||1|1|0|0
codex-cli--gpt-5.6-sol--pi|1|98|0.898|0.898|0.898|1|493.5|2|1|0|1
gemini-3.7-flash|2|423|0.068|0.767|0.417|0||1|1|0|0
glm-5.3-flash|2|181|0.727|0.788|0.758|1||1|1|0|0
gpt-5.6-sol|1|70|0.786|0.786|0.786|1|443.2|2|1|0|1
grok-4.6|1|116|0.655|0.655|0.655|0||1|1|0|0
qwen3.8-flash|1|51|0.569|0.569|0.569|1||1|1|0|0
random-baseline|2|1430|0.403|0.404|0.404|0||1|1|0|0
vista-claude-opus-5|1|75|0.68|0.68|0.68|1||1|1|0|0
vista-codex-gpt-5.6-sol|1|26|0.885|0.885|0.885|0||1|1|0|0

q p10/p50/p90 0.403 0.727 0.885
reads/action min   0.000 med   0.884 max   1.353
osc          min   0.000 med   0.026 max   0.069
keys         min   2.000 med   7.000 max  13.000
ttfa         min   0.480 med  18.380 max 219.500
gap50        min   1.400 med   7.840 max  21.540
apers        min   2.589 med   5.226 max  36.000
escapes bigmap 8 exit_secs 4 no exit secs,fade unknown: 10
grade(quality)median 0.727

### repetition-flag IDs (run ids reused as copy?)
none

### exposure-free cost check: never-started rows excluded: 5
   ever-none probe-lap10 60 time
   ever-none probe-lap9 60 time
   ever-none claude-sonnet-4.6 1200 never started
   ever-none gpt-5.2-codex 1200 never started
