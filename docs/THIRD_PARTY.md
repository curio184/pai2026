# 出典と利用条件

独自コードと第三者由来の素材・パッチを区別して配布します。リポジトリ全体へ一律に新しいライセンスを付与することはしていません。

| 使用物 | 出典・利用条件 | 配布内の対応 |
| --- | --- | --- |
| StampFly ecosystem | [固定リビジョン](https://github.com/M5Fly-kanazawa/stampfly_ecosystem/tree/9467f1a156326b95a01383e11c44dd665a55b536)、MIT | 物理シーンの機体メッシュ、XML、シーン内の機体形状。`assets/STAMPFLY_LICENSE.txt`を保持 |
| ArduPilot | [固定リビジョン](https://github.com/ArduPilot/ardupilot/tree/38687117133582049734ebd39f8a7af6f487716a)、GPL-3.0-or-later | `ardupilot_bridge/esp32_wifi_locks.patch`。`assets/ARDUPILOT_COPYING.txt`を保持。ファームウェア実行バイナリは配布しない |
| MakeHuman | [システム素材一覧](https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html)、使用素材はCC0 | 人物・衣服・髪・目・リグ。素材一覧とハッシュは`assets/civic_sources/`。MakeHumanプログラム本体のAGPLと素材のCC0を区別 |
| Poly Haven | [素材ライセンス](https://polyhaven.com/license)、CC0 | worn_plaster_wall、concrete_floor_02、red_brick_03のテクスチャ。出典とハッシュは`assets/civic_sources/sources.json` |
| SmolVLA | `lerobot/smolvla_base`、基盤モデルの固定リビジョン等は`THIRD_PARTY.json` | モデル重みは同梱しない。追加学習のコード・条件・記録を収録 |
| SSDlite | torchvision公式の人物検出モデル | 推論記録に使用重みのハッシュを保持。重みは同梱せず公式配布元から取得 |
| Blender、MuJoCo、LeRobot、PyTorch等 | それぞれの上流ライセンス | 依存ソフトウェアとして使用。実行環境一式や第三者バイナリの再配布は行わない |

室内の配置、破損表現、照明、カメラ、衣服の色、動画の図解と編集は本プロジェクトで制作しています。人物はCG素材であり、実在の被災者を撮影したものではありません。

最終動画のナレーションはOpenAIの生成音声です。音楽はプロジェクト内の処理で合成しています。既存楽曲や実在人物の声を録音・複製したものではありません。音声ファイルとフォントファイルはこのコード配布には含めていません。

第三者の著作権表示は維持します。ローカルアカウント名や開発環境のパスの除去は、それらの著作権表示の削除とは区別しています。

モデル重みを追加配布する場合には、取得した正確なリビジョンの利用条件を別途確認する必要があります。この配布物は重みの再配布許諾を付与するものではありません。
