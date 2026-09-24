#!/usr/bin/env bash
# Downloads the SIL OFL fonts used by the renderer into assets/fonts/.
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p fonts && cd fonts
raw=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sSL -o Anton.ttf        $raw/anton/Anton-Regular.ttf
curl -sSL -o BebasNeue.ttf    $raw/bebasneue/BebasNeue-Regular.ttf
curl -sSL -o PressStart2P.ttf $raw/pressstart2p/PressStart2P-Regular.ttf
# static weights (the variable fonts ignore weight in Skia), served as WOFF by the Google Fonts CSS API
UA="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30"
get() { curl -sSL -o "$3" "$(curl -sS -A "$UA" "https://fonts.googleapis.com/css?family=$1:$2" | grep -o 'https://[^)]*' | head -1)"; }
get Nunito 400 Nunito-400.woff; get Nunito 800 Nunito-800.woff; get Nunito 900 Nunito-900.woff
get JetBrains+Mono 400 JBM-400.woff; get JetBrains+Mono 800 JBM-800.woff
get Playfair+Display 700i Playfair-700i.woff; get Inter 800 Inter-800.woff
ls -la
