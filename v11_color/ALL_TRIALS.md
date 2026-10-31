# 追加検証の全実行

開発確認と最終評価を分け、失敗も含めて記載しています。動画はv1.0のままです。未実行は失敗として扱わず、別に記載します。

| 区分 | 試験 | モデル | 結果 | 停止時間 | 目標点への最短距離 | 記録 |
| --- | --- | --- | --- | --- | --- | --- |
| dev_train01 | dev01_blue | v1.1 | 失敗 | 0.942秒 | 0.131m | [採点・記録](runs/dev_train01/dev01_blue_v1.1/record/search_score.json) |
| dev_train01 | dev01_red | v1.1 | 成功 | 6.135秒 | 0.180m | [採点・記録](runs/dev_train01/dev01_red_v1.1/record/search_score.json) |
| dev_train01 | dev02_blue | v1.1 | 失敗 | 3.348秒 | 0.005m | [採点・記録](runs/dev_train01/dev02_blue_v1.1/record/search_score.json) |
| dev_train01 | dev02_red | v1.1 | 成功 | 3.628秒 | 0.039m | [採点・記録](runs/dev_train01/dev02_red_v1.1/record/search_score.json) |
| dev_train01 | primitive_blue | v1.1 | 失敗 | 3.669秒 | 0.128m | [採点・記録](runs/dev_train01/primitive_blue_v1.1/record/physical_score.json) |
| dev_train01 | primitive_red | v1.1 | 失敗 | 1.784秒 | 0.157m | [採点・記録](runs/dev_train01/primitive_red_v1.1/record/physical_score.json) |
| dev_train01 | primitive_turns | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train01/primitive_turns_v1.1/record/physical_score.json) |
| dev_train01 | primitive_left | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train01/primitive_left_v1.1/record/physical_score.json) |
| dev_train02 | dev01_blue | v1.1 | 成功 | 4.009秒 | 0.095m | [採点・記録](runs/dev_train02/dev01_blue_v1.1/record/search_score.json) |
| dev_train02 | dev01_red | v1.1 | 成功 | 3.849秒 | 0.035m | [採点・記録](runs/dev_train02/dev01_red_v1.1/record/search_score.json) |
| dev_train02 | dev02_blue | v1.1 | 失敗 | 3.909秒 | 0.076m | [採点・記録](runs/dev_train02/dev02_blue_v1.1/record/search_score.json) |
| dev_train02 | dev02_red | v1.1 | 成功 | 3.869秒 | 0.062m | [採点・記録](runs/dev_train02/dev02_red_v1.1/record/search_score.json) |
| dev_train02 | primitive_blue | v1.1 | 成功 | 4.331秒 | 0.116m | [採点・記録](runs/dev_train02/primitive_blue_v1.1/record/physical_score.json) |
| dev_train02 | primitive_red | v1.1 | 成功 | 5.152秒 | 0.071m | [採点・記録](runs/dev_train02/primitive_red_v1.1/record/physical_score.json) |
| dev_train02 | primitive_turns | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train02/primitive_turns_v1.1/record/physical_score.json) |
| dev_train02 | primitive_left | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train02/primitive_left_v1.1/record/physical_score.json) |
| dev_train03 | dev01_blue | v1.1 | 成功 | 5.834秒 | 0.034m | [採点・記録](runs/dev_train03/dev01_blue_v1.1/record/search_score.json) |
| dev_train03 | dev01_red | v1.1 | 成功 | 3.749秒 | 0.011m | [採点・記録](runs/dev_train03/dev01_red_v1.1/record/search_score.json) |
| dev_train03 | dev02_blue | v1.1 | 成功 | 3.869秒 | 0.030m | [採点・記録](runs/dev_train03/dev02_blue_v1.1/record/search_score.json) |
| dev_train03 | dev02_red | v1.1 | 成功 | 3.809秒 | 0.082m | [採点・記録](runs/dev_train03/dev02_red_v1.1/record/search_score.json) |
| dev_train03 | primitive_blue | v1.1 | 成功 | 4.551秒 | 0.053m | [採点・記録](runs/dev_train03/primitive_blue_v1.1/record/physical_score.json) |
| dev_train03 | primitive_red | v1.1 | 成功 | 4.932秒 | 0.029m | [採点・記録](runs/dev_train03/primitive_red_v1.1/record/physical_score.json) |
| dev_train03 | primitive_turns | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train03/primitive_turns_v1.1/record/physical_score.json) |
| dev_train03 | primitive_left | v1.1 | 成功 | - | - | [採点・記録](runs/dev_train03/primitive_left_v1.1/record/physical_score.json) |
| heldout_train03 | H01 | v1.0 | 失敗 | 0.000秒 | 1.487m | [採点・記録](runs/heldout_train03/H01_v1.0/record/search_score.json) |
| heldout_train03 | H01 | v1.1 | 失敗 | 0.000秒 | 2.823m | [採点・記録](runs/heldout_train03/H01_v1.1/record/search_score.json) |
| heldout_train03 | H02 | v1.1 | 成功 | 3.989秒 | 0.015m | [採点・記録](runs/heldout_train03/H02_v1.1/record/search_score.json) |
| heldout_train03 | H02 | v1.0 | 失敗 | 0.000秒 | 1.569m | [採点・記録](runs/heldout_train03/H02_v1.0/record/search_score.json) |
| heldout_train03 | H03 | v1.0 | 失敗 | 0.000秒 | 0.525m | [採点・記録](runs/heldout_train03/H03_v1.0/record/search_score.json) |
| heldout_train03 | H03 | v1.1 | 成功 | 4.090秒 | 0.023m | [採点・記録](runs/heldout_train03/H03_v1.1/record/search_score.json) |
| heldout_train03 | H04 | v1.1 | 成功 | 3.769秒 | 0.158m | [採点・記録](runs/heldout_train03/H04_v1.1/record/search_score.json) |
| heldout_train03 | H04 | v1.0 | 失敗 | 0.000秒 | 0.857m | [採点・記録](runs/heldout_train03/H04_v1.0/record/search_score.json) |
| heldout_train03 | H05 | v1.0 | 失敗 | 5.834秒 | 0.100m | [採点・記録](runs/heldout_train03/H05_v1.0/record/search_score.json) |
| heldout_train03 | H05 | v1.1 | 失敗 | 6.515秒 | 0.007m | [採点・記録](runs/heldout_train03/H05_v1.1/record/search_score.json) |
| heldout_train03 | H06 | v1.1 | 失敗 | 0.000秒 | 2.339m | [採点・記録](runs/heldout_train03/H06_v1.1/record/search_score.json) |
| heldout_train03 | H06 | v1.0 | 失敗 | 0.000秒 | 2.413m | [採点・記録](runs/heldout_train03/H06_v1.0/record/search_score.json) |
| heldout_train03 | H07 | v1.0 | 失敗 | 4.270秒 | 0.096m | [採点・記録](runs/heldout_train03/H07_v1.0/record/search_score.json) |
| heldout_train03 | H07 | v1.1 | 失敗 | 4.310秒 | 0.026m | [採点・記録](runs/heldout_train03/H07_v1.1/record/search_score.json) |
| heldout_train03 | H08 | v1.1 | 成功 | 4.751秒 | 0.025m | [採点・記録](runs/heldout_train03/H08_v1.1/record/search_score.json) |
| heldout_train03 | H08 | v1.0 | 成功 | 4.130秒 | 0.095m | [採点・記録](runs/heldout_train03/H08_v1.0/record/search_score.json) |
| heldout_train03 | H09 | v1.0 | 失敗 | 0.000秒 | 0.350m | [採点・記録](runs/heldout_train03/H09_v1.0/record/search_score.json) |
| heldout_train03 | H09 | v1.1 | 失敗 | 6.515秒 | 0.036m | [採点・記録](runs/heldout_train03/H09_v1.1/record/search_score.json) |
| heldout_train03 | H10 | v1.1 | 失敗 | 2.245秒 | 0.035m | [採点・記録](runs/heldout_train03/H10_v1.1/record/search_score.json) |
| heldout_train03 | H10 | v1.0 | 失敗 | 0.000秒 | 1.279m | [採点・記録](runs/heldout_train03/H10_v1.0/record/search_score.json) |
| heldout_train03 | H11 | v1.0 | 失敗 | 0.000秒 | 0.633m | [採点・記録](runs/heldout_train03/H11_v1.0/record/search_score.json) |
| heldout_train03 | H11 | v1.1 | 失敗 | 4.290秒 | 0.037m | [採点・記録](runs/heldout_train03/H11_v1.1/record/search_score.json) |
| heldout_train03 | H12 | v1.1 | 成功 | 4.009秒 | 0.084m | [採点・記録](runs/heldout_train03/H12_v1.1/record/search_score.json) |
| heldout_train03 | H12 | v1.0 | 失敗 | 0.000秒 | 1.682m | [採点・記録](runs/heldout_train03/H12_v1.0/record/search_score.json) |
| heldout_train03 | H13 | v1.0 | 成功 | 6.395秒 | 0.121m | [採点・記録](runs/heldout_train03/H13_v1.0/record/search_score.json) |
| heldout_train03 | H13 | v1.1 | 失敗 | 3.608秒 | 0.005m | [採点・記録](runs/heldout_train03/H13_v1.1/record/search_score.json) |
| heldout_train03 | H14 | v1.1 | 失敗 | 0.000秒 | 0.287m | [採点・記録](runs/heldout_train03/H14_v1.1/record/search_score.json) |
| heldout_train03 | H14 | v1.0 | 失敗 | 4.350秒 | 0.016m | [採点・記録](runs/heldout_train03/H14_v1.0/record/search_score.json) |
| heldout_train03 | H15 | v1.0 | 失敗 | 0.080秒 | 0.209m | [採点・記録](runs/heldout_train03/H15_v1.0/record/search_score.json) |
| heldout_train03 | H15 | v1.1 | 失敗 | 0.000秒 | 1.695m | [採点・記録](runs/heldout_train03/H15_v1.1/record/search_score.json) |
| heldout_train03 | H16 | v1.1 | 成功 | 4.310秒 | 0.033m | [採点・記録](runs/heldout_train03/H16_v1.1/record/search_score.json) |
| heldout_train03 | H16 | v1.0 | 失敗 | 4.250秒 | 0.121m | [採点・記録](runs/heldout_train03/H16_v1.0/record/search_score.json) |
| known_failure_train03 | T3_blue_retest | v1.1 | 成功 | 6.736秒 | 0.015m | [採点・記録](runs/known_failure_train03/T3_blue_retest_v1.1/record/search_score.json) |
| regression_train03 | clear_blue | v1.1 | 成功 | 3.809秒 | 0.037m | [採点・記録](runs/regression_train03/clear_blue_v1.1/record/search_score.json) |
| regression_train03 | clear_red | v1.1 | 成功 | 4.872秒 | 0.011m | [採点・記録](runs/regression_train03/clear_red_v1.1/record/search_score.json) |
| regression_train03 | fog_light_blue | v1.1 | 成功 | 3.909秒 | 0.106m | [採点・記録](runs/regression_train03/fog_light_blue_v1.1/record/search_score.json) |
| regression_train03 | fog_dense_blue | v1.1 | 成功 | 3.749秒 | 0.091m | [採点・記録](runs/regression_train03/fog_dense_blue_v1.1/record/search_score.json) |
| regression_train03 | dust_blue | v1.1 | 成功 | 3.929秒 | 0.059m | [採点・記録](runs/regression_train03/dust_blue_v1.1/record/search_score.json) |

未実行：0件。


停止時間と最短距離は、対象者の前に設定した目標点に対する値です。人物そのものへの距離ではありません。
詳細な条件、全画像、生成した動作、事後採点は各試験フォルダーにあります。
