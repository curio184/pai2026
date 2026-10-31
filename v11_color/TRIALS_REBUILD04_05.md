# rebuild04・rebuild05 の全試験

失敗も含め、実行したすべての飛行です。採点は飛行後に記録から行いました（`scripts/score_rebuild04.py`／`scripts/score_rebuild05.py`）。

## rebuild04 試運転（遅れ0.4秒、開発用の配置）

スイートは旧採点プログラムで動いたため一度「失敗」と記録され、`score_rebuild04.py` で採点し直した（`runs/rebuild04_smoke/rescored.json`）。

| ID | 区分 | 場面 | 対象 | 判定 | 停止の継続（秒） | 記録 |
|---|---|---|---|---|---|---|
| S01_dev01_blue | smoke_dev | dev01 | blue | 成功 | 6.03 | [記録](runs/rebuild04_smoke/S01_dev01_blue/record/) |
| S02_dev02_red | smoke_dev | dev02 | red | 成功 | 4.25 | [記録](runs/rebuild04_smoke/S02_dev02_red/record/) |
| S03_primitive_left | smoke_dev | clear | left | 成功 |  | [記録](runs/rebuild04_smoke/S03_primitive_left/record/) |

## rebuild04 本番（遅れ0.4秒）

未学習の配置15/16、動画の場面7/9。登録した基準（動画の場面9/9）に届かなかった。

| ID | 区分 | 場面 | 対象 | 判定 | 停止の継続（秒） | 記録 |
|---|---|---|---|---|---|---|
| R4F01 | matched_unseen | heldout_r04_01 | blue | 成功 | 4.37 | [記録](runs/rebuild04_final/R4F01/record/) |
| R4F02 | matched_unseen | heldout_r04_01 | blue | 成功 | 3.41 | [記録](runs/rebuild04_final/R4F02/record/) |
| R4F03 | matched_unseen | heldout_r04_01 | red | 成功 | 4.13 | [記録](runs/rebuild04_final/R4F03/record/) |
| R4F04 | matched_unseen | heldout_r04_01 | red | 成功 | 4.19 | [記録](runs/rebuild04_final/R4F04/record/) |
| R4F05 | matched_unseen | heldout_r04_02 | blue | 成功 | 5.65 | [記録](runs/rebuild04_final/R4F05/record/) |
| R4F06 | matched_unseen | heldout_r04_02 | blue | 失敗 | 5.91 | [記録](runs/rebuild04_final/R4F06/record/) |
| R4F07 | matched_unseen | heldout_r04_02 | red | 成功 | 3.95 | [記録](runs/rebuild04_final/R4F07/record/) |
| R4F08 | matched_unseen | heldout_r04_02 | red | 成功 | 3.99 | [記録](runs/rebuild04_final/R4F08/record/) |
| R4F09 | matched_unseen | heldout_r04_03 | blue | 成功 | 4.21 | [記録](runs/rebuild04_final/R4F09/record/) |
| R4F10 | matched_unseen | heldout_r04_03 | blue | 成功 | 3.99 | [記録](runs/rebuild04_final/R4F10/record/) |
| R4F11 | matched_unseen | heldout_r04_03 | red | 成功 | 5.71 | [記録](runs/rebuild04_final/R4F11/record/) |
| R4F12 | matched_unseen | heldout_r04_03 | red | 成功 | 4.09 | [記録](runs/rebuild04_final/R4F12/record/) |
| R4F13 | matched_unseen | heldout_r04_04 | blue | 成功 | 3.97 | [記録](runs/rebuild04_final/R4F13/record/) |
| R4F14 | matched_unseen | heldout_r04_04 | blue | 成功 | 4.15 | [記録](runs/rebuild04_final/R4F14/record/) |
| R4F15 | matched_unseen | heldout_r04_04 | red | 成功 | 5.51 | [記録](runs/rebuild04_final/R4F15/record/) |
| R4F16 | matched_unseen | heldout_r04_04 | red | 成功 | 4.03 | [記録](runs/rebuild04_final/R4F16/record/) |
| primitive_blue | video_regression | clear | blue | 成功 | 5.89 | [記録](runs/rebuild04_final/primitive_blue/record/) |
| primitive_red | video_regression | clear | red | 成功 | 6.23 | [記録](runs/rebuild04_final/primitive_red/record/) |
| primitive_turns | video_regression | clear | turns | 成功 |  | [記録](runs/rebuild04_final/primitive_turns/record/) |
| primitive_left | video_regression | clear | left | 成功 |  | [記録](runs/rebuild04_final/primitive_left/record/) |
| search_clear_blue | video_regression | clear | blue | 成功 | 3.95 | [記録](runs/rebuild04_final/search_clear_blue/record/) |
| search_clear_red | video_regression | clear | red | 失敗 | 1.98 | [記録](runs/rebuild04_final/search_clear_red/record/) |
| search_fog_light_blue | video_regression | fog_light | blue | 失敗 | 2.45 | [記録](runs/rebuild04_final/search_fog_light_blue/record/) |
| search_fog_dense_blue | video_regression | fog_dense | blue | 成功 | 4.15 | [記録](runs/rebuild04_final/search_fog_dense_blue/record/) |
| search_dust_blue | video_regression | dust | blue | 成功 | 3.95 | [記録](runs/rebuild04_final/search_dust_blue/record/) |
| known_T3_blue | known_failure | known_swapped | blue | 成功 | 4.25 | [記録](runs/rebuild04_final/known_T3_blue/record/) |

## rebuild05 本番（遅れ0.2秒、最終）

未学習の配置16/16、動画の場面8/9。登録した基準のうち動画の場面9/9には届かなかったが、結果はそのまま報告している。

| ID | 区分 | 場面 | 対象 | 判定 | 停止の継続（秒） | 記録 |
|---|---|---|---|---|---|---|
| R5F01 | matched_unseen | heldout_r05_01 | blue | 成功 | 5.65 | [記録](runs/rebuild05_final/R5F01/record/) |
| R5F02 | matched_unseen | heldout_r05_01 | blue | 成功 | 3.99 | [記録](runs/rebuild05_final/R5F02/record/) |
| R5F03 | matched_unseen | heldout_r05_01 | red | 成功 | 5.51 | [記録](runs/rebuild05_final/R5F03/record/) |
| R5F04 | matched_unseen | heldout_r05_01 | red | 成功 | 4.09 | [記録](runs/rebuild05_final/R5F04/record/) |
| R5F05 | matched_unseen | heldout_r05_02 | blue | 成功 | 5.03 | [記録](runs/rebuild05_final/R5F05/record/) |
| R5F06 | matched_unseen | heldout_r05_02 | blue | 成功 | 4.01 | [記録](runs/rebuild05_final/R5F06/record/) |
| R5F07 | matched_unseen | heldout_r05_02 | red | 成功 | 3.99 | [記録](runs/rebuild05_final/R5F07/record/) |
| R5F08 | matched_unseen | heldout_r05_02 | red | 成功 | 7.62 | [記録](runs/rebuild05_final/R5F08/record/) |
| R5F09 | matched_unseen | heldout_r05_03 | blue | 成功 | 3.93 | [記録](runs/rebuild05_final/R5F09/record/) |
| R5F10 | matched_unseen | heldout_r05_03 | blue | 成功 | 5.55 | [記録](runs/rebuild05_final/R5F10/record/) |
| R5F11 | matched_unseen | heldout_r05_03 | red | 成功 | 4.17 | [記録](runs/rebuild05_final/R5F11/record/) |
| R5F12 | matched_unseen | heldout_r05_03 | red | 成功 | 8.24 | [記録](runs/rebuild05_final/R5F12/record/) |
| R5F13 | matched_unseen | heldout_r05_04 | blue | 成功 | 4.07 | [記録](runs/rebuild05_final/R5F13/record/) |
| R5F14 | matched_unseen | heldout_r05_04 | blue | 成功 | 8.40 | [記録](runs/rebuild05_final/R5F14/record/) |
| R5F15 | matched_unseen | heldout_r05_04 | red | 成功 | 8.34 | [記録](runs/rebuild05_final/R5F15/record/) |
| R5F16 | matched_unseen | heldout_r05_04 | red | 成功 | 3.89 | [記録](runs/rebuild05_final/R5F16/record/) |
| primitive_blue | video_regression | clear | blue | 成功 | 3.97 | [記録](runs/rebuild05_final/primitive_blue/record/) |
| primitive_red | video_regression | clear | red | 成功 | 4.01 | [記録](runs/rebuild05_final/primitive_red/record/) |
| primitive_turns | video_regression | clear | turns | 成功 |  | [記録](runs/rebuild05_final/primitive_turns/record/) |
| primitive_left | video_regression | clear | left | 成功 |  | [記録](runs/rebuild05_final/primitive_left/record/) |
| search_clear_blue | video_regression | clear | blue | 成功 | 3.99 | [記録](runs/rebuild05_final/search_clear_blue/record/) |
| search_clear_red | video_regression | clear | red | 成功 | 4.27 | [記録](runs/rebuild05_final/search_clear_red/record/) |
| search_fog_light_blue | video_regression | fog_light | blue | 失敗 | 2.77 | [記録](runs/rebuild05_final/search_fog_light_blue/record/) |
| search_fog_dense_blue | video_regression | fog_dense | blue | 成功 | 3.85 | [記録](runs/rebuild05_final/search_fog_dense_blue/record/) |
| search_dust_blue | video_regression | dust | blue | 成功 | 5.67 | [記録](runs/rebuild05_final/search_dust_blue/record/) |
| known_T3_blue | known_failure | known_swapped | blue | 成功 | 5.07 | [記録](runs/rebuild05_final/known_T3_blue/record/) |
