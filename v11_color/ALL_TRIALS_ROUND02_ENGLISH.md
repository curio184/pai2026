# 追加検証の全実行

失敗した最初の最終評価、開発確認、英語へ統一した次の最終評価を分けて記載しています。成功例だけの一覧ではありません。動画はv1.0のままです。

| 区分 | 試験 | 重み | 指示 | 結果 | 停止時間 | 目標点への最短距離 | 人物への最小距離 | 記録 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev_train01 | dev01_blue | train01 | 英日併記 | 失敗 | 0.942秒 | 0.131m | 0.606m | [採点・記録](runs/dev_train01/dev01_blue_v1.1/record/search_score.json) |
| dev_train01 | dev01_red | train01 | 英日併記 | 成功 | 6.135秒 | 0.180m | 0.781m | [採点・記録](runs/dev_train01/dev01_red_v1.1/record/search_score.json) |
| dev_train01 | dev02_blue | train01 | 英日併記 | 失敗 | 3.348秒 | 0.005m | 0.421m | [採点・記録](runs/dev_train01/dev02_blue_v1.1/record/search_score.json) |
| dev_train01 | dev02_red | train01 | 英日併記 | 成功 | 3.628秒 | 0.039m | 0.547m | [採点・記録](runs/dev_train01/dev02_red_v1.1/record/search_score.json) |
| dev_train01 | primitive_blue | train01 | 英日併記 | 失敗 | 3.669秒 | 0.128m | 0.375m | [採点・記録](runs/dev_train01/primitive_blue_v1.1/record/physical_score.json) |
| dev_train01 | primitive_red | train01 | 英日併記 | 失敗 | 1.784秒 | 0.157m | 0.553m | [採点・記録](runs/dev_train01/primitive_red_v1.1/record/physical_score.json) |
| dev_train01 | primitive_turns | train01 | 英日併記 | 成功 | - | - | 1.910m | [採点・記録](runs/dev_train01/primitive_turns_v1.1/record/physical_score.json) |
| dev_train01 | primitive_left | train01 | 英日併記 | 成功 | - | - | 2.790m | [採点・記録](runs/dev_train01/primitive_left_v1.1/record/physical_score.json) |
| dev_train02 | dev01_blue | train02 | 英日併記 | 成功 | 4.009秒 | 0.095m | 0.542m | [採点・記録](runs/dev_train02/dev01_blue_v1.1/record/search_score.json) |
| dev_train02 | dev01_red | train02 | 英日併記 | 成功 | 3.849秒 | 0.035m | 0.523m | [採点・記録](runs/dev_train02/dev01_red_v1.1/record/search_score.json) |
| dev_train02 | dev02_blue | train02 | 英日併記 | 失敗 | 3.909秒 | 0.076m | 0.433m | [採点・記録](runs/dev_train02/dev02_blue_v1.1/record/search_score.json) |
| dev_train02 | dev02_red | train02 | 英日併記 | 成功 | 3.869秒 | 0.062m | 0.562m | [採点・記録](runs/dev_train02/dev02_red_v1.1/record/search_score.json) |
| dev_train02 | primitive_blue | train02 | 英日併記 | 成功 | 4.331秒 | 0.116m | 0.621m | [採点・記録](runs/dev_train02/primitive_blue_v1.1/record/physical_score.json) |
| dev_train02 | primitive_red | train02 | 英日併記 | 成功 | 5.152秒 | 0.071m | 0.632m | [採点・記録](runs/dev_train02/primitive_red_v1.1/record/physical_score.json) |
| dev_train02 | primitive_turns | train02 | 英日併記 | 成功 | - | - | 1.699m | [採点・記録](runs/dev_train02/primitive_turns_v1.1/record/physical_score.json) |
| dev_train02 | primitive_left | train02 | 英日併記 | 成功 | - | - | 2.620m | [採点・記録](runs/dev_train02/primitive_left_v1.1/record/physical_score.json) |
| dev_train03 | dev01_blue | train03 | 英日併記 | 成功 | 5.834秒 | 0.034m | 0.696m | [採点・記録](runs/dev_train03/dev01_blue_v1.1/record/search_score.json) |
| dev_train03 | dev01_red | train03 | 英日併記 | 成功 | 3.749秒 | 0.011m | 0.675m | [採点・記録](runs/dev_train03/dev01_red_v1.1/record/search_score.json) |
| dev_train03 | dev02_blue | train03 | 英日併記 | 成功 | 3.869秒 | 0.030m | 0.668m | [採点・記録](runs/dev_train03/dev02_blue_v1.1/record/search_score.json) |
| dev_train03 | dev02_red | train03 | 英日併記 | 成功 | 3.809秒 | 0.082m | 0.649m | [採点・記録](runs/dev_train03/dev02_red_v1.1/record/search_score.json) |
| dev_train03 | primitive_blue | train03 | 英日併記 | 成功 | 4.551秒 | 0.053m | 0.695m | [採点・記録](runs/dev_train03/primitive_blue_v1.1/record/physical_score.json) |
| dev_train03 | primitive_red | train03 | 英日併記 | 成功 | 4.932秒 | 0.029m | 0.734m | [採点・記録](runs/dev_train03/primitive_red_v1.1/record/physical_score.json) |
| dev_train03 | primitive_turns | train03 | 英日併記 | 成功 | - | - | 1.609m | [採点・記録](runs/dev_train03/primitive_turns_v1.1/record/physical_score.json) |
| dev_train03 | primitive_left | train03 | 英日併記 | 成功 | - | - | 2.578m | [採点・記録](runs/dev_train03/primitive_left_v1.1/record/physical_score.json) |
| dev_train04_en | dev01_blue | train04_en | 英語 | 成功 | 3.949秒 | 0.025m | 0.615m | [採点・記録](runs/dev_train04_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train04_en | dev01_red | train04_en | 英語 | 成功 | 3.629秒 | 0.003m | 0.699m | [採点・記録](runs/dev_train04_en/dev01_red_v1.1/record/search_score.json) |
| dev_train04_en | dev02_blue | train04_en | 英語 | 成功 | 8.741秒 | 0.046m | 0.713m | [採点・記録](runs/dev_train04_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train04_en | dev02_red | train04_en | 英語 | 成功 | 4.070秒 | 0.076m | 0.718m | [採点・記録](runs/dev_train04_en/dev02_red_v1.1/record/search_score.json) |
| dev_train04_en | primitive_blue | train04_en | 英語 | 成功 | 3.509秒 | 0.024m | 0.728m | [採点・記録](runs/dev_train04_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train04_en | primitive_red | train04_en | 英語 | 成功 | 3.849秒 | 0.043m | 0.717m | [採点・記録](runs/dev_train04_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train04_en | primitive_turns | train04_en | 英語 | 成功 | - | - | 3.046m | [採点・記録](runs/dev_train04_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train04_en | primitive_left | train04_en | 英語 | 成功 | - | - | 2.841m | [採点・記録](runs/dev_train04_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train05_en | dev01_blue | train05_en | 英語 | 成功 | 4.009秒 | 0.004m | 0.699m | [採点・記録](runs/dev_train05_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train05_en | dev01_red | train05_en | 英語 | 成功 | 3.729秒 | 0.029m | 0.618m | [採点・記録](runs/dev_train05_en/dev01_red_v1.1/record/search_score.json) |
| dev_train05_en | dev02_blue | train05_en | 英語 | 成功 | 3.749秒 | 0.017m | 0.658m | [採点・記録](runs/dev_train05_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train05_en | dev02_red | train05_en | 英語 | 成功 | 5.433秒 | 0.038m | 0.652m | [採点・記録](runs/dev_train05_en/dev02_red_v1.1/record/search_score.json) |
| dev_train05_en | primitive_blue | train05_en | 英語 | 成功 | 3.488秒 | 0.010m | 0.734m | [採点・記録](runs/dev_train05_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train05_en | primitive_red | train05_en | 英語 | 成功 | 3.909秒 | 0.032m | 0.750m | [採点・記録](runs/dev_train05_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train05_en | primitive_turns | train05_en | 英語 | 成功 | - | - | 2.743m | [採点・記録](runs/dev_train05_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train05_en | primitive_left | train05_en | 英語 | 成功 | - | - | 2.956m | [採点・記録](runs/dev_train05_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train06_en | dev01_blue | train06_en | 英語 | 成功 | 6.997秒 | 0.012m | 0.646m | [採点・記録](runs/dev_train06_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train06_en | dev01_red | train06_en | 英語 | 成功 | 3.729秒 | 0.038m | 0.727m | [採点・記録](runs/dev_train06_en/dev01_red_v1.1/record/search_score.json) |
| dev_train06_en | dev02_blue | train06_en | 英語 | 成功 | 7.298秒 | 0.008m | 0.601m | [採点・記録](runs/dev_train06_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train06_en | dev02_red | train06_en | 英語 | 成功 | 3.869秒 | 0.089m | 0.599m | [採点・記録](runs/dev_train06_en/dev02_red_v1.1/record/search_score.json) |
| dev_train06_en | primitive_blue | train06_en | 英語 | 成功 | 3.529秒 | 0.014m | 0.779m | [採点・記録](runs/dev_train06_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train06_en | primitive_red | train06_en | 英語 | 成功 | 3.749秒 | 0.025m | 0.738m | [採点・記録](runs/dev_train06_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train06_en | primitive_turns | train06_en | 英語 | 成功 | - | - | 2.813m | [採点・記録](runs/dev_train06_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train06_en | primitive_left | train06_en | 英語 | 成功 | - | - | 2.937m | [採点・記録](runs/dev_train06_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train07_en | dev01_blue | train07_en | 英語 | 成功 | 3.969秒 | 0.135m | 0.524m | [採点・記録](runs/dev_train07_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train07_en | dev01_red | train07_en | 英語 | 成功 | 3.869秒 | 0.017m | 0.567m | [採点・記録](runs/dev_train07_en/dev01_red_v1.1/record/search_score.json) |
| dev_train07_en | dev02_blue | train07_en | 英語 | 失敗 | 3.949秒 | 0.136m | 0.447m | [採点・記録](runs/dev_train07_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train07_en | dev02_red | train07_en | 英語 | 成功 | 3.949秒 | 0.066m | 0.491m | [採点・記録](runs/dev_train07_en/dev02_red_v1.1/record/search_score.json) |
| dev_train07_en | primitive_blue | train07_en | 英語 | 成功 | 3.909秒 | 0.110m | 0.643m | [採点・記録](runs/dev_train07_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train07_en | primitive_red | train07_en | 英語 | 成功 | 3.809秒 | 0.075m | 0.656m | [採点・記録](runs/dev_train07_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train07_en | primitive_turns | train07_en | 英語 | 成功 | - | - | 2.113m | [採点・記録](runs/dev_train07_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train07_en | primitive_left | train07_en | 英語 | 成功 | - | - | 2.542m | [採点・記録](runs/dev_train07_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train08_en | dev01_blue | train08_en_capped | 英語 | 実行基盤のエラー | 0.000秒 | 2.032m | 2.321m | [採点・記録](runs/dev_train08_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train08_en_capped | dev01_blue | train08_en_capped | 英語 | 成功 | 4.070秒 | 0.099m | 0.799m | [採点・記録](runs/dev_train08_en_capped/dev01_blue_v1.1/record/search_score.json) |
| dev_train08_en_capped | dev01_red | train08_en_capped | 英語 | 成功 | 3.929秒 | 0.087m | 0.562m | [採点・記録](runs/dev_train08_en_capped/dev01_red_v1.1/record/search_score.json) |
| dev_train08_en_capped | dev02_blue | train08_en_capped | 英語 | 成功 | 6.997秒 | 0.040m | 0.580m | [採点・記録](runs/dev_train08_en_capped/dev02_blue_v1.1/record/search_score.json) |
| dev_train08_en_capped | dev02_red | train08_en_capped | 英語 | 成功 | 3.990秒 | 0.040m | 0.570m | [採点・記録](runs/dev_train08_en_capped/dev02_red_v1.1/record/search_score.json) |
| dev_train08_en_capped | primitive_blue | train08_en_capped | 英語 | 成功 | 3.869秒 | 0.070m | 0.644m | [採点・記録](runs/dev_train08_en_capped/primitive_blue_v1.1/record/physical_score.json) |
| dev_train08_en_capped | primitive_red | train08_en_capped | 英語 | 成功 | 3.789秒 | 0.024m | 0.718m | [採点・記録](runs/dev_train08_en_capped/primitive_red_v1.1/record/physical_score.json) |
| dev_train08_en_capped | primitive_turns | train08_en_capped | 英語 | 成功 | - | - | 1.854m | [採点・記録](runs/dev_train08_en_capped/primitive_turns_v1.1/record/physical_score.json) |
| dev_train08_en_capped | primitive_left | train08_en_capped | 英語 | 成功 | - | - | 2.540m | [採点・記録](runs/dev_train08_en_capped/primitive_left_v1.1/record/physical_score.json) |
| dev_train09_en | dev01_blue | train09_en | 英語 | 成功 | 8.981秒 | 0.006m | 0.681m | [採点・記録](runs/dev_train09_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train09_en | dev01_red | train09_en | 英語 | 成功 | 3.949秒 | 0.033m | 0.603m | [採点・記録](runs/dev_train09_en/dev01_red_v1.1/record/search_score.json) |
| dev_train09_en | dev02_blue | train09_en | 英語 | 成功 | 3.829秒 | 0.029m | 0.633m | [採点・記録](runs/dev_train09_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train09_en | dev02_red | train09_en | 英語 | 成功 | 4.010秒 | 0.048m | 0.652m | [採点・記録](runs/dev_train09_en/dev02_red_v1.1/record/search_score.json) |
| dev_train09_en | primitive_blue | train09_en | 英語 | 成功 | 3.749秒 | 0.018m | 0.731m | [採点・記録](runs/dev_train09_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train09_en | primitive_red | train09_en | 英語 | 成功 | 3.869秒 | 0.012m | 0.711m | [採点・記録](runs/dev_train09_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train09_en | primitive_turns | train09_en | 英語 | 失敗 | - | - | 2.829m | [採点・記録](runs/dev_train09_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train09_en | primitive_left | train09_en | 英語 | 成功 | - | - | 2.757m | [採点・記録](runs/dev_train09_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train10_en | dev01_blue | train10_en | 英語 | 成功 | 3.949秒 | 0.038m | 0.608m | [採点・記録](runs/dev_train10_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train10_en | dev01_red | train10_en | 英語 | 成功 | 3.889秒 | 0.034m | 0.712m | [採点・記録](runs/dev_train10_en/dev01_red_v1.1/record/search_score.json) |
| dev_train10_en | dev02_blue | train10_en | 英語 | 成功 | 4.030秒 | 0.025m | 0.636m | [採点・記録](runs/dev_train10_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train10_en | dev02_red | train10_en | 英語 | 成功 | 3.949秒 | 0.029m | 0.693m | [採点・記録](runs/dev_train10_en/dev02_red_v1.1/record/search_score.json) |
| dev_train10_en | primitive_blue | train10_en | 英語 | 成功 | 3.589秒 | 0.036m | 0.637m | [採点・記録](runs/dev_train10_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train10_en | primitive_red | train10_en | 英語 | 成功 | 3.869秒 | 0.045m | 0.713m | [採点・記録](runs/dev_train10_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train10_en | primitive_turns | train10_en | 英語 | 成功 | - | - | 2.318m | [採点・記録](runs/dev_train10_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train10_en | primitive_left | train10_en | 英語 | 成功 | - | - | 2.729m | [採点・記録](runs/dev_train10_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train11_en | dev01_blue | train11_en | 英語 | 成功 | 4.030秒 | 0.046m | 0.626m | [採点・記録](runs/dev_train11_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train11_en | dev01_red | train11_en | 英語 | 成功 | 3.889秒 | 0.052m | 0.619m | [採点・記録](runs/dev_train11_en/dev01_red_v1.1/record/search_score.json) |
| dev_train11_en | dev02_blue | train11_en | 英語 | 成功 | 3.990秒 | 0.140m | 0.654m | [採点・記録](runs/dev_train11_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train11_en | dev02_red | train11_en | 英語 | 成功 | 3.989秒 | 0.024m | 0.634m | [採点・記録](runs/dev_train11_en/dev02_red_v1.1/record/search_score.json) |
| dev_train11_en | primitive_blue | train11_en | 英語 | 成功 | 3.929秒 | 0.039m | 0.742m | [採点・記録](runs/dev_train11_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train11_en | primitive_red | train11_en | 英語 | 成功 | 3.930秒 | 0.073m | 0.743m | [採点・記録](runs/dev_train11_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train11_en | primitive_turns | train11_en | 英語 | 成功 | - | - | 2.306m | [採点・記録](runs/dev_train11_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train11_en | primitive_left | train11_en | 英語 | 成功 | - | - | 2.929m | [採点・記録](runs/dev_train11_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train12_en | dev01_blue | train12_en | 英語 | 失敗 | 0.000秒 | 2.023m | 2.274m | [採点・記録](runs/dev_train12_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train12_en | dev01_red | train12_en | 英語 | 成功 | 7.638秒 | 0.029m | 0.697m | [採点・記録](runs/dev_train12_en/dev01_red_v1.1/record/search_score.json) |
| dev_train12_en | dev02_blue | train12_en | 英語 | 成功 | 3.989秒 | 0.010m | 0.493m | [採点・記録](runs/dev_train12_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train12_en | dev02_red | train12_en | 英語 | 成功 | 9.402秒 | 0.051m | 0.709m | [採点・記録](runs/dev_train12_en/dev02_red_v1.1/record/search_score.json) |
| dev_train12_en | primitive_blue | train12_en | 英語 | 成功 | 3.889秒 | 0.044m | 0.682m | [採点・記録](runs/dev_train12_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train12_en | primitive_red | train12_en | 英語 | 成功 | 3.970秒 | 0.076m | 0.779m | [採点・記録](runs/dev_train12_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train12_en | primitive_turns | train12_en | 英語 | 成功 | - | - | 2.417m | [採点・記録](runs/dev_train12_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train12_en | primitive_left | train12_en | 英語 | 成功 | - | - | 2.906m | [採点・記録](runs/dev_train12_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train13_en | dev01_blue | train13_en | 英語 | 成功 | 8.660秒 | 0.060m | 0.720m | [採点・記録](runs/dev_train13_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train13_en | dev01_red | train13_en | 英語 | 成功 | 3.689秒 | 0.026m | 0.714m | [採点・記録](runs/dev_train13_en/dev01_red_v1.1/record/search_score.json) |
| dev_train13_en | dev02_blue | train13_en | 英語 | 成功 | 3.669秒 | 0.016m | 0.676m | [採点・記録](runs/dev_train13_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train13_en | dev02_red | train13_en | 英語 | 成功 | 7.016秒 | 0.098m | 0.806m | [採点・記録](runs/dev_train13_en/dev02_red_v1.1/record/search_score.json) |
| dev_train13_en | primitive_blue | train13_en | 英語 | 成功 | 3.709秒 | 0.066m | 0.944m | [採点・記録](runs/dev_train13_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train13_en | primitive_red | train13_en | 英語 | 成功 | 3.990秒 | 0.005m | 0.660m | [採点・記録](runs/dev_train13_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train13_en | primitive_turns | train13_en | 英語 | 成功 | - | - | 2.437m | [採点・記録](runs/dev_train13_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train13_en | primitive_left | train13_en | 英語 | 成功 | - | - | 2.935m | [採点・記録](runs/dev_train13_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train14_en | dev01_blue | train14_en | 英語 | 成功 | 3.949秒 | 0.053m | 0.908m | [採点・記録](runs/dev_train14_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train14_en | dev01_red | train14_en | 英語 | 成功 | 3.629秒 | 0.015m | 0.694m | [採点・記録](runs/dev_train14_en/dev01_red_v1.1/record/search_score.json) |
| dev_train14_en | dev02_blue | train14_en | 英語 | 成功 | 3.869秒 | 0.083m | 0.552m | [採点・記録](runs/dev_train14_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train14_en | dev02_red | train14_en | 英語 | 失敗 | 7.016秒 | 0.004m | 0.844m | [採点・記録](runs/dev_train14_en/dev02_red_v1.1/record/search_score.json) |
| dev_train14_en | primitive_blue | train14_en | 英語 | 成功 | 3.829秒 | 0.128m | 0.961m | [採点・記録](runs/dev_train14_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train14_en | primitive_red | train14_en | 英語 | 成功 | 3.929秒 | 0.026m | 0.713m | [採点・記録](runs/dev_train14_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train14_en | primitive_turns | train14_en | 英語 | 成功 | - | - | 2.146m | [採点・記録](runs/dev_train14_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train14_en | primitive_left | train14_en | 英語 | 失敗 | - | - | 2.907m | [採点・記録](runs/dev_train14_en/primitive_left_v1.1/record/physical_score.json) |
| dev_train15_en | dev01_blue | train15_en | 英語 | 成功 | 4.029秒 | 0.062m | 0.687m | [採点・記録](runs/dev_train15_en/dev01_blue_v1.1/record/search_score.json) |
| dev_train15_en | dev01_red | train15_en | 英語 | 成功 | 3.789秒 | 0.004m | 0.631m | [採点・記録](runs/dev_train15_en/dev01_red_v1.1/record/search_score.json) |
| dev_train15_en | dev02_blue | train15_en | 英語 | 成功 | 3.849秒 | 0.096m | 0.654m | [採点・記録](runs/dev_train15_en/dev02_blue_v1.1/record/search_score.json) |
| dev_train15_en | dev02_red | train15_en | 英語 | 成功 | 3.889秒 | 0.017m | 0.759m | [採点・記録](runs/dev_train15_en/dev02_red_v1.1/record/search_score.json) |
| dev_train15_en | primitive_blue | train15_en | 英語 | 成功 | 3.829秒 | 0.047m | 0.890m | [採点・記録](runs/dev_train15_en/primitive_blue_v1.1/record/physical_score.json) |
| dev_train15_en | primitive_red | train15_en | 英語 | 成功 | 3.909秒 | 0.011m | 0.713m | [採点・記録](runs/dev_train15_en/primitive_red_v1.1/record/physical_score.json) |
| dev_train15_en | primitive_turns | train15_en | 英語 | 成功 | - | - | 2.152m | [採点・記録](runs/dev_train15_en/primitive_turns_v1.1/record/physical_score.json) |
| dev_train15_en | primitive_left | train15_en | 英語 | 成功 | - | - | 2.889m | [採点・記録](runs/dev_train15_en/primitive_left_v1.1/record/physical_score.json) |
| heldout_train03 | H01 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 1.487m | 0.807m | [採点・記録](runs/heldout_train03/H01_v1.0/record/search_score.json) |
| heldout_train03 | H01 | train03 | 英日併記 | 失敗 | 0.000秒 | 2.823m | 2.935m | [採点・記録](runs/heldout_train03/H01_v1.1/record/search_score.json) |
| heldout_train03 | H02 | train03 | 英日併記 | 成功 | 3.989秒 | 0.015m | 0.691m | [採点・記録](runs/heldout_train03/H02_v1.1/record/search_score.json) |
| heldout_train03 | H02 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 1.569m | 0.271m | [採点・記録](runs/heldout_train03/H02_v1.0/record/search_score.json) |
| heldout_train03 | H03 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 0.525m | 0.914m | [採点・記録](runs/heldout_train03/H03_v1.0/record/search_score.json) |
| heldout_train03 | H03 | train03 | 英日併記 | 成功 | 4.090秒 | 0.023m | 0.813m | [採点・記録](runs/heldout_train03/H03_v1.1/record/search_score.json) |
| heldout_train03 | H04 | train03 | 英日併記 | 成功 | 3.769秒 | 0.158m | 0.801m | [採点・記録](runs/heldout_train03/H04_v1.1/record/search_score.json) |
| heldout_train03 | H04 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 0.857m | 1.066m | [採点・記録](runs/heldout_train03/H04_v1.0/record/search_score.json) |
| heldout_train03 | H05 | v1.0 | 英日併記 | 失敗 | 5.834秒 | 0.100m | 0.686m | [採点・記録](runs/heldout_train03/H05_v1.0/record/search_score.json) |
| heldout_train03 | H05 | train03 | 英日併記 | 失敗 | 6.515秒 | 0.007m | 0.802m | [採点・記録](runs/heldout_train03/H05_v1.1/record/search_score.json) |
| heldout_train03 | H06 | train03 | 英日併記 | 失敗 | 0.000秒 | 2.339m | 0.842m | [採点・記録](runs/heldout_train03/H06_v1.1/record/search_score.json) |
| heldout_train03 | H06 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 2.413m | 0.928m | [採点・記録](runs/heldout_train03/H06_v1.0/record/search_score.json) |
| heldout_train03 | H07 | v1.0 | 英日併記 | 失敗 | 4.270秒 | 0.096m | 0.732m | [採点・記録](runs/heldout_train03/H07_v1.0/record/search_score.json) |
| heldout_train03 | H07 | train03 | 英日併記 | 失敗 | 4.310秒 | 0.026m | 0.814m | [採点・記録](runs/heldout_train03/H07_v1.1/record/search_score.json) |
| heldout_train03 | H08 | train03 | 英日併記 | 成功 | 4.751秒 | 0.025m | 0.596m | [採点・記録](runs/heldout_train03/H08_v1.1/record/search_score.json) |
| heldout_train03 | H08 | v1.0 | 英日併記 | 成功 | 4.130秒 | 0.095m | 0.581m | [採点・記録](runs/heldout_train03/H08_v1.0/record/search_score.json) |
| heldout_train03 | H09 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 0.350m | 0.596m | [採点・記録](runs/heldout_train03/H09_v1.0/record/search_score.json) |
| heldout_train03 | H09 | train03 | 英日併記 | 失敗 | 6.515秒 | 0.036m | 0.867m | [採点・記録](runs/heldout_train03/H09_v1.1/record/search_score.json) |
| heldout_train03 | H10 | train03 | 英日併記 | 失敗 | 2.245秒 | 0.035m | 0.807m | [採点・記録](runs/heldout_train03/H10_v1.1/record/search_score.json) |
| heldout_train03 | H10 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 1.279m | 0.301m | [採点・記録](runs/heldout_train03/H10_v1.0/record/search_score.json) |
| heldout_train03 | H11 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 0.633m | 0.387m | [採点・記録](runs/heldout_train03/H11_v1.0/record/search_score.json) |
| heldout_train03 | H11 | train03 | 英日併記 | 失敗 | 4.290秒 | 0.037m | 0.741m | [採点・記録](runs/heldout_train03/H11_v1.1/record/search_score.json) |
| heldout_train03 | H12 | train03 | 英日併記 | 成功 | 4.009秒 | 0.084m | 0.971m | [採点・記録](runs/heldout_train03/H12_v1.1/record/search_score.json) |
| heldout_train03 | H12 | v1.0 | 英日併記 | 失敗 | 0.000秒 | 1.682m | 2.497m | [採点・記録](runs/heldout_train03/H12_v1.0/record/search_score.json) |
| heldout_train03 | H13 | v1.0 | 英日併記 | 成功 | 6.395秒 | 0.121m | 0.679m | [採点・記録](runs/heldout_train03/H13_v1.0/record/search_score.json) |
| heldout_train03 | H13 | train03 | 英日併記 | 失敗 | 3.608秒 | 0.005m | 0.739m | [採点・記録](runs/heldout_train03/H13_v1.1/record/search_score.json) |
| heldout_train03 | H14 | train03 | 英日併記 | 失敗 | 0.000秒 | 0.287m | 0.459m | [採点・記録](runs/heldout_train03/H14_v1.1/record/search_score.json) |
| heldout_train03 | H14 | v1.0 | 英日併記 | 失敗 | 4.350秒 | 0.016m | 0.848m | [採点・記録](runs/heldout_train03/H14_v1.0/record/search_score.json) |
| heldout_train03 | H15 | v1.0 | 英日併記 | 失敗 | 0.080秒 | 0.209m | 0.828m | [採点・記録](runs/heldout_train03/H15_v1.0/record/search_score.json) |
| heldout_train03 | H15 | train03 | 英日併記 | 失敗 | 0.000秒 | 1.695m | 0.472m | [採点・記録](runs/heldout_train03/H15_v1.1/record/search_score.json) |
| heldout_train03 | H16 | train03 | 英日併記 | 成功 | 4.310秒 | 0.033m | 0.607m | [採点・記録](runs/heldout_train03/H16_v1.1/record/search_score.json) |
| heldout_train03 | H16 | v1.0 | 英日併記 | 失敗 | 4.250秒 | 0.121m | 0.398m | [採点・記録](runs/heldout_train03/H16_v1.0/record/search_score.json) |
| known_failure_train03 | T3_blue_retest | train03 | 英日併記 | 成功 | 6.736秒 | 0.015m | 0.782m | [採点・記録](runs/known_failure_train03/T3_blue_retest_v1.1/record/search_score.json) |
| regression_train03 | clear_blue | train03 | 英日併記 | 成功 | 3.809秒 | 0.037m | 0.667m | [採点・記録](runs/regression_train03/clear_blue_v1.1/record/search_score.json) |
| regression_train03 | clear_red | train03 | 英日併記 | 成功 | 4.872秒 | 0.011m | 0.654m | [採点・記録](runs/regression_train03/clear_red_v1.1/record/search_score.json) |
| regression_train03 | fog_light_blue | train03 | 英日併記 | 成功 | 3.909秒 | 0.106m | 0.647m | [採点・記録](runs/regression_train03/fog_light_blue_v1.1/record/search_score.json) |
| regression_train03 | fog_dense_blue | train03 | 英日併記 | 成功 | 3.749秒 | 0.091m | 0.747m | [採点・記録](runs/regression_train03/fog_dense_blue_v1.1/record/search_score.json) |
| regression_train03 | dust_blue | train03 | 英日併記 | 成功 | 3.929秒 | 0.059m | 0.713m | [採点・記録](runs/regression_train03/dust_blue_v1.1/record/search_score.json) |
| stress_train04_en | H01 | train04_en | 英語 | 成功 | 4.050秒 | 0.181m | 1.032m | [採点・記録](runs/stress_train04_en/H01_v1.1/record/search_score.json) |
| stress_train04_en | H02 | train04_en | 英語 | 成功 | 4.009秒 | 0.062m | 0.702m | [採点・記録](runs/stress_train04_en/H02_v1.1/record/search_score.json) |
| stress_train04_en | H03 | train04_en | 英語 | 成功 | 3.669秒 | 0.047m | 0.946m | [採点・記録](runs/stress_train04_en/H03_v1.1/record/search_score.json) |
| stress_train04_en | H04 | train04_en | 英語 | 成功 | 3.849秒 | 0.197m | 0.880m | [採点・記録](runs/stress_train04_en/H04_v1.1/record/search_score.json) |
| stress_train04_en | H05 | train04_en | 英語 | 成功 | 3.909秒 | 0.002m | 0.851m | [採点・記録](runs/stress_train04_en/H05_v1.1/record/search_score.json) |
| stress_train04_en | H06 | train04_en | 英語 | 失敗 | 0.000秒 | 1.736m | 1.463m | [採点・記録](runs/stress_train04_en/H06_v1.1/record/search_score.json) |
| stress_train04_en | H07 | train04_en | 英語 | 失敗 | 4.390秒 | 0.052m | 0.852m | [採点・記録](runs/stress_train04_en/H07_v1.1/record/search_score.json) |
| stress_train04_en | H08 | train04_en | 英語 | 成功 | 4.190秒 | 0.007m | 0.730m | [採点・記録](runs/stress_train04_en/H08_v1.1/record/search_score.json) |
| stress_train04_en | H09 | train04_en | 英語 | 成功 | 4.010秒 | 0.021m | 0.766m | [採点・記録](runs/stress_train04_en/H09_v1.1/record/search_score.json) |
| stress_train04_en | H10 | train04_en | 英語 | 成功 | 7.037秒 | 0.019m | 0.783m | [採点・記録](runs/stress_train04_en/H10_v1.1/record/search_score.json) |
| stress_train04_en | H11 | train04_en | 英語 | 失敗 | 4.190秒 | 0.048m | 0.714m | [採点・記録](runs/stress_train04_en/H11_v1.1/record/search_score.json) |
| stress_train04_en | H12 | train04_en | 英語 | 失敗 | 0.000秒 | 1.854m | 2.638m | [採点・記録](runs/stress_train04_en/H12_v1.1/record/search_score.json) |
| stress_train04_en | H13 | train04_en | 英語 | 成功 | 9.843秒 | 0.006m | 0.762m | [採点・記録](runs/stress_train04_en/H13_v1.1/record/search_score.json) |
| stress_train04_en | H14 | train04_en | 英語 | 失敗 | 4.350秒 | 0.030m | 0.910m | [採点・記録](runs/stress_train04_en/H14_v1.1/record/search_score.json) |
| stress_train04_en | H15 | train04_en | 英語 | 失敗 | 0.000秒 | 1.585m | 2.365m | [採点・記録](runs/stress_train04_en/H15_v1.1/record/search_score.json) |
| stress_train04_en | H16 | train04_en | 英語 | 成功 | 4.090秒 | 0.059m | 0.573m | [採点・記録](runs/stress_train04_en/H16_v1.1/record/search_score.json) |
| stress_train05_en | H01 | train05_en | 英語 | 成功 | 4.049秒 | 0.166m | 1.060m | [採点・記録](runs/stress_train05_en/H01_v1.1/record/search_score.json) |
| stress_train05_en | H02 | train05_en | 英語 | 成功 | 7.016秒 | 0.007m | 0.644m | [採点・記録](runs/stress_train05_en/H02_v1.1/record/search_score.json) |
| stress_train05_en | H03 | train05_en | 英語 | 成功 | 3.990秒 | 0.063m | 0.957m | [採点・記録](runs/stress_train05_en/H03_v1.1/record/search_score.json) |
| stress_train05_en | H04 | train05_en | 英語 | 成功 | 6.996秒 | 0.080m | 0.848m | [採点・記録](runs/stress_train05_en/H04_v1.1/record/search_score.json) |
| stress_train05_en | H05 | train05_en | 英語 | 成功 | 4.591秒 | 0.036m | 0.873m | [採点・記録](runs/stress_train05_en/H05_v1.1/record/search_score.json) |
| stress_train05_en | H06 | train05_en | 英語 | 失敗 | 0.000秒 | 2.036m | 0.651m | [採点・記録](runs/stress_train05_en/H06_v1.1/record/search_score.json) |
| stress_train05_en | H07 | train05_en | 英語 | 成功 | 4.330秒 | 0.042m | 0.914m | [採点・記録](runs/stress_train05_en/H07_v1.1/record/search_score.json) |
| stress_train05_en | H08 | train05_en | 英語 | 成功 | 4.811秒 | 0.044m | 0.525m | [採点・記録](runs/stress_train05_en/H08_v1.1/record/search_score.json) |
| stress_train05_en | H09 | train05_en | 英語 | 失敗 | 2.927秒 | 0.033m | 0.575m | [採点・記録](runs/stress_train05_en/H09_v1.1/record/search_score.json) |
| stress_train05_en | H10 | train05_en | 英語 | 成功 | 7.017秒 | 0.111m | 0.775m | [採点・記録](runs/stress_train05_en/H10_v1.1/record/search_score.json) |
| stress_train05_en | H11 | train05_en | 英語 | 失敗 | 3.588秒 | 0.025m | 0.818m | [採点・記録](runs/stress_train05_en/H11_v1.1/record/search_score.json) |
| stress_train05_en | H12 | train05_en | 英語 | 成功 | 4.009秒 | 0.071m | 0.959m | [採点・記録](runs/stress_train05_en/H12_v1.1/record/search_score.json) |
| stress_train05_en | H13 | train05_en | 英語 | 成功 | 3.930秒 | 0.000m | 0.799m | [採点・記録](runs/stress_train05_en/H13_v1.1/record/search_score.json) |
| stress_train05_en | H14 | train05_en | 英語 | 失敗 | 7.397秒 | 0.047m | 0.944m | [採点・記録](runs/stress_train05_en/H14_v1.1/record/search_score.json) |
| stress_train05_en | H15 | train05_en | 英語 | 失敗 | 0.000秒 | 1.743m | 2.523m | [採点・記録](runs/stress_train05_en/H15_v1.1/record/search_score.json) |
| stress_train05_en | H16 | train05_en | 英語 | 成功 | 4.250秒 | 0.053m | 0.550m | [採点・記録](runs/stress_train05_en/H16_v1.1/record/search_score.json) |
| stress_train06_en | H01 | train06_en | 英語 | 失敗 | 0.421秒 | 0.244m | 1.126m | [採点・記録](runs/stress_train06_en/H01_v1.1/record/search_score.json) |
| stress_train06_en | H02 | train06_en | 英語 | 成功 | 3.769秒 | 0.029m | 0.537m | [採点・記録](runs/stress_train06_en/H02_v1.1/record/search_score.json) |
| stress_train06_en | H03 | train06_en | 英語 | 成功 | 4.050秒 | 0.062m | 0.908m | [採点・記録](runs/stress_train06_en/H03_v1.1/record/search_score.json) |
| stress_train06_en | H04 | train06_en | 英語 | 成功 | 3.849秒 | 0.158m | 0.832m | [採点・記録](runs/stress_train06_en/H04_v1.1/record/search_score.json) |
| stress_train06_en | H05 | train06_en | 英語 | 成功 | 3.809秒 | 0.122m | 0.813m | [採点・記録](runs/stress_train06_en/H05_v1.1/record/search_score.json) |
| stress_train06_en | H06 | train06_en | 英語 | 失敗 | 0.000秒 | 1.903m | 1.190m | [採点・記録](runs/stress_train06_en/H06_v1.1/record/search_score.json) |
| stress_train06_en | H07 | train06_en | 英語 | 成功 | 4.049秒 | 0.113m | 0.964m | [採点・記録](runs/stress_train06_en/H07_v1.1/record/search_score.json) |
| stress_train06_en | H08 | train06_en | 英語 | 成功 | 4.170秒 | 0.115m | 0.574m | [採点・記録](runs/stress_train06_en/H08_v1.1/record/search_score.json) |
| stress_train06_en | H09 | train06_en | 英語 | 失敗 | 6.996秒 | 0.041m | 0.525m | [採点・記録](runs/stress_train06_en/H09_v1.1/record/search_score.json) |
| stress_train06_en | H10 | train06_en | 英語 | 成功 | 3.248秒 | 0.152m | 0.822m | [採点・記録](runs/stress_train06_en/H10_v1.1/record/search_score.json) |
| stress_train06_en | H11 | train06_en | 英語 | 失敗 | 3.087秒 | 0.031m | 0.773m | [採点・記録](runs/stress_train06_en/H11_v1.1/record/search_score.json) |
| stress_train06_en | H12 | train06_en | 英語 | 失敗 | 2.646秒 | 0.077m | 0.971m | [採点・記録](runs/stress_train06_en/H12_v1.1/record/search_score.json) |
| stress_train06_en | H13 | train06_en | 英語 | 成功 | 3.930秒 | 0.040m | 0.816m | [採点・記録](runs/stress_train06_en/H13_v1.1/record/search_score.json) |
| stress_train06_en | H14 | train06_en | 英語 | 失敗 | 3.368秒 | 0.062m | 0.910m | [採点・記録](runs/stress_train06_en/H14_v1.1/record/search_score.json) |
| stress_train06_en | H15 | train06_en | 英語 | 失敗 | 0.000秒 | 0.257m | 1.096m | [採点・記録](runs/stress_train06_en/H15_v1.1/record/search_score.json) |
| stress_train06_en | H16 | train06_en | 英語 | 成功 | 4.290秒 | 0.123m | 0.462m | [採点・記録](runs/stress_train06_en/H16_v1.1/record/search_score.json) |
| stress_train08_en_capped | H01 | train08_en_capped | 英語 | 失敗 | 0.000秒 | 2.823m | 2.935m | [採点・記録](runs/stress_train08_en_capped/H01_v1.1/record/search_score.json) |
| stress_train08_en_capped | H02 | train08_en_capped | 英語 | 成功 | 4.069秒 | 0.021m | 0.702m | [採点・記録](runs/stress_train08_en_capped/H02_v1.1/record/search_score.json) |
| stress_train08_en_capped | H03 | train08_en_capped | 英語 | 成功 | 4.050秒 | 0.085m | 0.985m | [採点・記録](runs/stress_train08_en_capped/H03_v1.1/record/search_score.json) |
| stress_train08_en_capped | H04 | train08_en_capped | 英語 | 失敗 | 3.809秒 | 0.150m | 0.820m | [採点・記録](runs/stress_train08_en_capped/H04_v1.1/record/search_score.json) |
| stress_train08_en_capped | H05 | train08_en_capped | 英語 | 失敗 | 3.769秒 | 0.021m | 0.794m | [採点・記録](runs/stress_train08_en_capped/H05_v1.1/record/search_score.json) |
| stress_train08_en_capped | H06 | train08_en_capped | 英語 | 失敗 | 0.000秒 | 2.455m | 0.982m | [採点・記録](runs/stress_train08_en_capped/H06_v1.1/record/search_score.json) |
| stress_train08_en_capped | H07 | train08_en_capped | 英語 | 失敗 | 0.000秒 | 2.072m | 2.709m | [採点・記録](runs/stress_train08_en_capped/H07_v1.1/record/search_score.json) |
| stress_train08_en_capped | H08 | train08_en_capped | 英語 | 成功 | 4.611秒 | 0.045m | 0.675m | [採点・記録](runs/stress_train08_en_capped/H08_v1.1/record/search_score.json) |
| stress_train08_en_capped | H09 | train08_en_capped | 英語 | 成功 | 3.889秒 | 0.030m | 0.762m | [採点・記録](runs/stress_train08_en_capped/H09_v1.1/record/search_score.json) |
| stress_train08_en_capped | H10 | train08_en_capped | 英語 | 成功 | 4.070秒 | 0.102m | 0.843m | [採点・記録](runs/stress_train08_en_capped/H10_v1.1/record/search_score.json) |
| stress_train08_en_capped | H11 | train08_en_capped | 英語 | 失敗 | 3.789秒 | 0.012m | 0.855m | [採点・記録](runs/stress_train08_en_capped/H11_v1.1/record/search_score.json) |
| stress_train08_en_capped | H12 | train08_en_capped | 英語 | 成功 | 3.709秒 | 0.099m | 0.997m | [採点・記録](runs/stress_train08_en_capped/H12_v1.1/record/search_score.json) |
| stress_train08_en_capped | H13 | train08_en_capped | 英語 | 失敗 | 12.269秒 | 0.023m | 0.735m | [採点・記録](runs/stress_train08_en_capped/H13_v1.1/record/search_score.json) |
| stress_train08_en_capped | H14 | train08_en_capped | 英語 | 成功 | 4.350秒 | 0.060m | 0.950m | [採点・記録](runs/stress_train08_en_capped/H14_v1.1/record/search_score.json) |
| stress_train08_en_capped | H15 | train08_en_capped | 英語 | 失敗 | 0.000秒 | 1.777m | 0.381m | [採点・記録](runs/stress_train08_en_capped/H15_v1.1/record/search_score.json) |
| stress_train08_en_capped | H16 | train08_en_capped | 英語 | 成功 | 4.370秒 | 0.052m | 0.513m | [採点・記録](runs/stress_train08_en_capped/H16_v1.1/record/search_score.json) |
| stress_train10_en | H01 | train10_en | 英語 | 成功 | 3.989秒 | 0.115m | 0.935m | [採点・記録](runs/stress_train10_en/H01_v1.1/record/search_score.json) |
| stress_train10_en | H02 | train10_en | 英語 | 成功 | 3.949秒 | 0.031m | 0.710m | [採点・記録](runs/stress_train10_en/H02_v1.1/record/search_score.json) |
| stress_train10_en | H03 | train10_en | 英語 | 成功 | 3.889秒 | 0.059m | 0.956m | [採点・記録](runs/stress_train10_en/H03_v1.1/record/search_score.json) |
| stress_train10_en | H04 | train10_en | 英語 | 成功 | 5.453秒 | 0.091m | 0.839m | [採点・記録](runs/stress_train10_en/H04_v1.1/record/search_score.json) |
| stress_train10_en | H05 | train10_en | 英語 | 成功 | 3.789秒 | 0.019m | 0.889m | [採点・記録](runs/stress_train10_en/H05_v1.1/record/search_score.json) |
| stress_train10_en | H06 | train10_en | 英語 | 失敗 | 0.000秒 | 2.076m | 0.613m | [採点・記録](runs/stress_train10_en/H06_v1.1/record/search_score.json) |
| stress_train10_en | H07 | train10_en | 英語 | 失敗 | 4.170秒 | 0.096m | 0.888m | [採点・記録](runs/stress_train10_en/H07_v1.1/record/search_score.json) |
| stress_train10_en | H08 | train10_en | 英語 | 成功 | 4.130秒 | 0.001m | 0.644m | [採点・記録](runs/stress_train10_en/H08_v1.1/record/search_score.json) |
| stress_train10_en | H09 | train10_en | 英語 | 成功 | 6.996秒 | 0.025m | 0.581m | [採点・記録](runs/stress_train10_en/H09_v1.1/record/search_score.json) |
| stress_train10_en | H10 | train10_en | 英語 | 成功 | 7.017秒 | 0.066m | 0.759m | [採点・記録](runs/stress_train10_en/H10_v1.1/record/search_score.json) |
| stress_train10_en | H11 | train10_en | 英語 | 成功 | 4.070秒 | 0.066m | 0.814m | [採点・記録](runs/stress_train10_en/H11_v1.1/record/search_score.json) |
| stress_train10_en | H12 | train10_en | 英語 | 失敗 | 0.000秒 | 1.609m | 2.378m | [採点・記録](runs/stress_train10_en/H12_v1.1/record/search_score.json) |
| stress_train10_en | H13 | train10_en | 英語 | 成功 | 3.909秒 | 0.053m | 0.834m | [採点・記録](runs/stress_train10_en/H13_v1.1/record/search_score.json) |
| stress_train10_en | H14 | train10_en | 英語 | 成功 | 3.749秒 | 0.088m | 0.943m | [採点・記録](runs/stress_train10_en/H14_v1.1/record/search_score.json) |
| stress_train10_en | H15 | train10_en | 英語 | 失敗 | 2.887秒 | 0.100m | 0.946m | [採点・記録](runs/stress_train10_en/H15_v1.1/record/search_score.json) |
| stress_train10_en | H16 | train10_en | 英語 | 成功 | 4.150秒 | 0.059m | 0.546m | [採点・記録](runs/stress_train10_en/H16_v1.1/record/search_score.json) |
| stress_train11_en | H01 | train11_en | 英語 | 成功 | 4.009秒 | 0.117m | 1.016m | [採点・記録](runs/stress_train11_en/H01_v1.1/record/search_score.json) |
| stress_train11_en | H02 | train11_en | 英語 | 成功 | 4.130秒 | 0.009m | 0.596m | [採点・記録](runs/stress_train11_en/H02_v1.1/record/search_score.json) |
| stress_train11_en | H03 | train11_en | 英語 | 成功 | 4.170秒 | 0.033m | 0.931m | [採点・記録](runs/stress_train11_en/H03_v1.1/record/search_score.json) |
| stress_train11_en | H04 | train11_en | 英語 | 成功 | 3.869秒 | 0.018m | 0.797m | [採点・記録](runs/stress_train11_en/H04_v1.1/record/search_score.json) |
| stress_train11_en | H05 | train11_en | 英語 | 成功 | 5.252秒 | 0.098m | 0.758m | [採点・記録](runs/stress_train11_en/H05_v1.1/record/search_score.json) |
| stress_train11_en | H06 | train11_en | 英語 | 失敗 | 0.000秒 | 2.198m | 0.762m | [採点・記録](runs/stress_train11_en/H06_v1.1/record/search_score.json) |
| stress_train11_en | H07 | train11_en | 英語 | 成功 | 4.170秒 | 0.114m | 0.910m | [採点・記録](runs/stress_train11_en/H07_v1.1/record/search_score.json) |
| stress_train11_en | H08 | train11_en | 英語 | 成功 | 4.290秒 | 0.061m | 0.646m | [採点・記録](runs/stress_train11_en/H08_v1.1/record/search_score.json) |
| stress_train11_en | H09 | train11_en | 英語 | 成功 | 3.829秒 | 0.050m | 0.539m | [採点・記録](runs/stress_train11_en/H09_v1.1/record/search_score.json) |
| stress_train11_en | H10 | train11_en | 英語 | 成功 | 5.032秒 | 0.099m | 0.759m | [採点・記録](runs/stress_train11_en/H10_v1.1/record/search_score.json) |
| stress_train11_en | H11 | train11_en | 英語 | 失敗 | 4.070秒 | 0.037m | 0.691m | [採点・記録](runs/stress_train11_en/H11_v1.1/record/search_score.json) |
| stress_train11_en | H12 | train11_en | 英語 | 失敗 | 0.000秒 | 1.626m | 2.424m | [採点・記録](runs/stress_train11_en/H12_v1.1/record/search_score.json) |
| stress_train11_en | H13 | train11_en | 英語 | 成功 | 3.990秒 | 0.018m | 0.846m | [採点・記録](runs/stress_train11_en/H13_v1.1/record/search_score.json) |
| stress_train11_en | H14 | train11_en | 英語 | 成功 | 4.651秒 | 0.087m | 0.942m | [採点・記録](runs/stress_train11_en/H14_v1.1/record/search_score.json) |
| stress_train11_en | H15 | train11_en | 英語 | 成功 | 3.428秒 | 0.040m | 0.923m | [採点・記録](runs/stress_train11_en/H15_v1.1/record/search_score.json) |
| stress_train11_en | H16 | train11_en | 英語 | 失敗 | 0.000秒 | 2.018m | 2.050m | [採点・記録](runs/stress_train11_en/H16_v1.1/record/search_score.json) |
| stress_train13_en | H01 | train13_en | 英語 | 失敗 | 6.976秒 | 0.077m | 0.856m | [採点・記録](runs/stress_train13_en/H01_v1.1/record/search_score.json) |
| stress_train13_en | H02 | train13_en | 英語 | 失敗 | 3.969秒 | 0.133m | 0.396m | [採点・記録](runs/stress_train13_en/H02_v1.1/record/search_score.json) |
| stress_train13_en | H03 | train13_en | 英語 | 成功 | 3.869秒 | 0.028m | 0.818m | [採点・記録](runs/stress_train13_en/H03_v1.1/record/search_score.json) |
| stress_train13_en | H04 | train13_en | 英語 | 成功 | 3.849秒 | 0.048m | 0.817m | [採点・記録](runs/stress_train13_en/H04_v1.1/record/search_score.json) |
| stress_train13_en | H05 | train13_en | 英語 | 成功 | 3.749秒 | 0.134m | 0.829m | [採点・記録](runs/stress_train13_en/H05_v1.1/record/search_score.json) |
| stress_train13_en | H06 | train13_en | 英語 | 失敗 | 4.050秒 | 0.141m | 0.834m | [採点・記録](runs/stress_train13_en/H06_v1.1/record/search_score.json) |
| stress_train13_en | H07 | train13_en | 英語 | 成功 | 6.375秒 | 0.212m | 0.721m | [採点・記録](runs/stress_train13_en/H07_v1.1/record/search_score.json) |
| stress_train13_en | H08 | train13_en | 英語 | 成功 | 3.428秒 | 0.200m | 0.628m | [採点・記録](runs/stress_train13_en/H08_v1.1/record/search_score.json) |
| stress_train13_en | H09 | train13_en | 英語 | 失敗 | 4.049秒 | 0.163m | 0.732m | [採点・記録](runs/stress_train13_en/H09_v1.1/record/search_score.json) |
| stress_train13_en | H10 | train13_en | 英語 | 成功 | 3.889秒 | 0.210m | 0.859m | [採点・記録](runs/stress_train13_en/H10_v1.1/record/search_score.json) |
| stress_train13_en | H11 | train13_en | 英語 | 失敗 | 2.947秒 | 0.149m | 0.947m | [採点・記録](runs/stress_train13_en/H11_v1.1/record/search_score.json) |
| stress_train13_en | H12 | train13_en | 英語 | 成功 | 4.250秒 | 0.193m | 1.092m | [採点・記録](runs/stress_train13_en/H12_v1.1/record/search_score.json) |
| stress_train13_en | H13 | train13_en | 英語 | 成功 | 3.709秒 | 0.096m | 0.806m | [採点・記録](runs/stress_train13_en/H13_v1.1/record/search_score.json) |
| stress_train13_en | H14 | train13_en | 英語 | 成功 | 4.270秒 | 0.122m | 0.941m | [採点・記録](runs/stress_train13_en/H14_v1.1/record/search_score.json) |
| stress_train13_en | H15 | train13_en | 英語 | 失敗 | 2.927秒 | 0.197m | 1.018m | [採点・記録](runs/stress_train13_en/H15_v1.1/record/search_score.json) |
| stress_train13_en | H16 | train13_en | 英語 | 失敗 | 0.902秒 | 0.182m | 0.656m | [採点・記録](runs/stress_train13_en/H16_v1.1/record/search_score.json) |
| stress_train15_en | H01 | train15_en | 英語 | 失敗 | 4.090秒 | 0.092m | 0.992m | [採点・記録](runs/stress_train15_en/H01_v1.1/record/search_score.json) |
| stress_train15_en | H02 | train15_en | 英語 | 成功 | 5.633秒 | 0.092m | 0.520m | [採点・記録](runs/stress_train15_en/H02_v1.1/record/search_score.json) |
| stress_train15_en | H03 | train15_en | 英語 | 成功 | 3.969秒 | 0.065m | 0.843m | [採点・記録](runs/stress_train15_en/H03_v1.1/record/search_score.json) |
| stress_train15_en | H04 | train15_en | 英語 | 成功 | 3.869秒 | 0.031m | 0.846m | [採点・記録](runs/stress_train15_en/H04_v1.1/record/search_score.json) |
| stress_train15_en | H05 | train15_en | 英語 | 失敗 | 2.365秒 | 0.164m | 0.864m | [採点・記録](runs/stress_train15_en/H05_v1.1/record/search_score.json) |
| stress_train15_en | H06 | train15_en | 英語 | 失敗 | 0.000秒 | 2.147m | 0.729m | [採点・記録](runs/stress_train15_en/H06_v1.1/record/search_score.json) |
| stress_train15_en | H07 | train15_en | 英語 | 成功 | 4.170秒 | 0.129m | 0.882m | [採点・記録](runs/stress_train15_en/H07_v1.1/record/search_score.json) |
| stress_train15_en | H08 | train15_en | 英語 | 失敗 | 0.000秒 | 0.353m | 0.770m | [採点・記録](runs/stress_train15_en/H08_v1.1/record/search_score.json) |
| stress_train15_en | H09 | train15_en | 英語 | 失敗 | 22.113秒 | 0.063m | 0.340m | [採点・記録](runs/stress_train15_en/H09_v1.1/record/search_score.json) |
| stress_train15_en | H10 | train15_en | 英語 | 失敗 | 4.210秒 | 0.166m | 0.734m | [採点・記録](runs/stress_train15_en/H10_v1.1/record/search_score.json) |
| stress_train15_en | H11 | train15_en | 英語 | 成功 | 5.894秒 | 0.155m | 0.876m | [採点・記録](runs/stress_train15_en/H11_v1.1/record/search_score.json) |
| stress_train15_en | H12 | train15_en | 英語 | 成功 | 3.969秒 | 0.114m | 1.008m | [採点・記録](runs/stress_train15_en/H12_v1.1/record/search_score.json) |
| stress_train15_en | H13 | train15_en | 英語 | 成功 | 3.829秒 | 0.058m | 0.785m | [採点・記録](runs/stress_train15_en/H13_v1.1/record/search_score.json) |
| stress_train15_en | H14 | train15_en | 英語 | 成功 | 4.370秒 | 0.051m | 0.929m | [採点・記録](runs/stress_train15_en/H14_v1.1/record/search_score.json) |
| stress_train15_en | H15 | train15_en | 英語 | 成功 | 3.468秒 | 0.125m | 1.022m | [採点・記録](runs/stress_train15_en/H15_v1.1/record/search_score.json) |
| stress_train15_en | H16 | train15_en | 英語 | 失敗 | 0.000秒 | 0.442m | 0.815m | [採点・記録](runs/stress_train15_en/H16_v1.1/record/search_score.json) |

実行済み：287件。条件付きで未実行：45件。未実行を失敗には数えません。

- dev_train08_en / dev01_red / v1.1
- dev_train08_en / dev02_blue / v1.1
- dev_train08_en / dev02_red / v1.1
- dev_train08_en / primitive_blue / v1.1
- dev_train08_en / primitive_red / v1.1
- dev_train08_en / primitive_turns / v1.1
- dev_train08_en / primitive_left / v1.1
- regression_train15_en / clear_blue / v1.1
- regression_train15_en / clear_red / v1.1
- regression_train15_en / fog_light_blue / v1.1
- regression_train15_en / fog_dense_blue / v1.1
- regression_train15_en / dust_blue / v1.1
- known_failure_train15_en / T3_blue_retest / v1.1
- heldout_round02_english_train15_en / R2H01 / v1.0
- heldout_round02_english_train15_en / R2H01 / v1.1
- heldout_round02_english_train15_en / R2H02 / v1.0
- heldout_round02_english_train15_en / R2H02 / v1.1
- heldout_round02_english_train15_en / R2H03 / v1.0
- heldout_round02_english_train15_en / R2H03 / v1.1
- heldout_round02_english_train15_en / R2H04 / v1.0
- heldout_round02_english_train15_en / R2H04 / v1.1
- heldout_round02_english_train15_en / R2H05 / v1.0
- heldout_round02_english_train15_en / R2H05 / v1.1
- heldout_round02_english_train15_en / R2H06 / v1.0
- heldout_round02_english_train15_en / R2H06 / v1.1
- heldout_round02_english_train15_en / R2H07 / v1.0
- heldout_round02_english_train15_en / R2H07 / v1.1
- heldout_round02_english_train15_en / R2H08 / v1.0
- heldout_round02_english_train15_en / R2H08 / v1.1
- heldout_round02_english_train15_en / R2H09 / v1.0
- heldout_round02_english_train15_en / R2H09 / v1.1
- heldout_round02_english_train15_en / R2H10 / v1.0
- heldout_round02_english_train15_en / R2H10 / v1.1
- heldout_round02_english_train15_en / R2H11 / v1.0
- heldout_round02_english_train15_en / R2H11 / v1.1
- heldout_round02_english_train15_en / R2H12 / v1.0
- heldout_round02_english_train15_en / R2H12 / v1.1
- heldout_round02_english_train15_en / R2H13 / v1.0
- heldout_round02_english_train15_en / R2H13 / v1.1
- heldout_round02_english_train15_en / R2H14 / v1.0
- heldout_round02_english_train15_en / R2H14 / v1.1
- heldout_round02_english_train15_en / R2H15 / v1.0
- heldout_round02_english_train15_en / R2H15 / v1.1
- heldout_round02_english_train15_en / R2H16 / v1.0
- heldout_round02_english_train15_en / R2H16 / v1.1

停止時間は接近期に採点条件を連続して満たした最長時間です。目標点への距離は、対象者の前0.9mの採点点への距離です。人物への最小距離は、飛行中にいずれかの人物へ近づいた最短の水平距離で、目標点への距離とは区別しています。
入力画像・生成した動作・機体状態・任務の工程・事後採点は、各試験フォルダーに保存しています。

最初の最終評価：`runs/heldout_train03`。その結果を用いた改善後の最終評価：`runs/heldout_round02_english_*`。両者を合算した成功率は報告しません。
英語の指示への変更は、次の学習と最終評価を始める前に登録しました。以前の英日併記の記録はそのまま残しています。

## 資源制限と中断・起動エラー

WSLの本プロジェクト処理を4 CPU・8GiB以下に制限し、優先度を下げて1件ずつ実行しています。条件導入前後を合算した性能評価は行いません。`train08_en_capped` は `train08_en` と同じ重みを使う実行用の名前です。

| 区分 | 記録 | 扱い |
| --- | --- | --- |
| 利用者の指示による中断 | [元記録](runs/dev_train08_en/dev01_blue_v1.1/outcome.json) | 採点は不成功。通常の性能試験とは分ける |
| 飛行前の起動エラー | [元記録](runs/dev_train08_en/dev01_blue_v1.1_startup_failed01/startup_failure.json) | 飛行・推論は未開始。成功率の分母に含めない |
| 飛行前の起動エラー | [元記録](runs/dev_train08_en_capped/primitive_red_v1.1_startup_failed01/startup_failure.json) | 飛行・推論は未開始。成功率の分母に含めない |

各試験の `resource_limits.json` と `resource_usage.json` に上限と使用量を記録しています。[集計](reports/bounded_execution_summary.json)
