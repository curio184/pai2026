# 再現手順と配布範囲

## 保存済み記録を検証する

READMEの手順で`requirements-verify.txt`をインストールし、`python verify.py`を実行します。入力画像386枚と5件の原ログ、判定に使う物理シーンはリポジトリに含まれます。保存済みの物理スコアを再利用せず、一時コピー上で再計算します。

`python verify.py --output verification_output/result.json`で検査結果を保存できます。元の記録を編集した場合は配布ハッシュの検査に失敗します。実験を追加する場合は、配布時の記録と別のフォルダーを使用してください。

## 新しい飛行を実行するための準備

新規飛行は、保存記録の検証より多くの準備が必要です。配布物だけでワンクリック実行できるとはしていません。

実験時の構成はWindows側のGPU推論・Blender 3.1.2と、WSL Ubuntu 22.04側のMuJoCo・ArduPilot SITLです。Python依存関係は`requirements_smolvla_lock.txt`、`requirements_sitl.txt`などに記録しています。CUDA版PyTorchは対応する配布インデックスが必要で、環境のCUDA・GPUに合わせて構築してください。

1. 同梱する別添`pai2026-scenes.zip`をリポジトリのルートに展開します。`assets/civic_realism/revision03.blend`と`rescue_search/scenes/*/scene.blend`が配置されます。
2. `THIRD_PARTY.json`に記載したリビジョンのStampFly ecosystemとArduPilotを取得します。構築用コードは`setup_sils.py`、`ardupilot_bridge/setup_ardupilot.py`、`ardupilot_bridge/setup_bridge.py`、`rescue_search/build_plant.py`です。外部チェックアウトとビルドの作業先を自分の環境に合わせて設定してください。
3. 追加学習済みのモデル一式を用意します。この配布物にはモデル重みや教師画像全件を含めていません。基盤モデルを取得するだけでは、今回の飛行と同じモデルになりません。学習処理・設定・記録を参照して環境とデータを構成する必要があります。
4. Windows側の`RESCUE_PROJECT_ROOT`にリポジトリの絶対パスを指定します。`RESCUE_BLENDER`でBlender実行ファイル、`RESCUE_WSL_DISTRO`でWSL名、`RESCUE_WSL_PYTHON`でWSL内のPython実行ファイルを指定できます。
5. `rescue_search/run_search.py --help`で実行引数を確認します。`--checkpoint`でモデル一式、`--name`で新しい試行名、`--profile blue`または`red`、`--conditions clear fog_light fog_dense dust`で条件を指定します。

例えば、前提となるビルド・シーン・モデルがそろった環境では次の形式です。

```powershell
$env:RESCUE_PROJECT_ROOT=(Get-Location).Path
$env:RESCUE_BLENDER='C:/Program Files/Blender Foundation/Blender 3.1/blender.exe'
$env:RESCUE_WSL_DISTRO='Ubuntu-22.04'
$env:RESCUE_WSL_PYTHON='/path/to/venv/bin/python'
python rescue_search/run_search.py --name new_trial --profile blue --conditions clear --checkpoint /path/to/checkpoint
```

これは新規環境での全工程を保証するインストーラーではありません。ソースには開発時の工程ごとの準備・診断スクリプトも含まれます。主な実行入口は上記のものです。

最終モデルのSHA-256：`d119adc57fa0c4681f4413b621d6321d27b000c6a3550c5b075bbbebc3d9a467`。
同じハッシュでも、GPU処理・タイミング・依存関係の差による新規飛行の完全一致は保証しません。

## 原本と公開版の区別

実験時のソース・シーンのハッシュは各試行の`manifest.json`に保存しています。公開版ではローカルパスを除き、実行パスの一部を環境変数に置き換えています。実行時スナップショットもパスを匿名化しています。元のソースハッシュと公開用ファイルのハッシュが一致しないものは、`SOURCE_PROVENANCE.json`で区別します。

Blenderファイルはパスを除去して再保存しているため、実験時とファイル全体のハッシュが異なります。`docs/SCENE_SANITIZATION.json`に、元ファイルと配布版のハッシュ、および形状・配置・材質ノード・内蔵画像の照合結果を記録しています。

原JPEG・物理ログの内容は変更していません。過去の開発・失敗記録は別添`pai2026-development-records.zip`に分離して保持しています。

## 動画編集

編集コードと最新の計画は収録していますが、全外部カメラのレンダリング済み連番画像、生成音声、動画本体はGit本体に含めていません。動画の完全な再書き出しにはそれらの中間素材を再生成する必要があります。

音声生成コードを使う場合だけOpenAI APIキーが必要です。環境変数`OPENAI_API_KEY`またはGit対象外のルート`.env`を使用します。記録検証・VLA推論・シミュレーション飛行にOpenAI APIキーは不要です。
