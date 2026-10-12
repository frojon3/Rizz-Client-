# Rizz Client

Struktura:
- `mod-1.21.1/`  - Rizz Core pod Minecraft 1.21.1
- `mod-1.21.11/` - Rizz Core pod Minecraft 1.21.11
- `launcher/`    - launcher (Python)
- `.github/workflows/build.yml` - automatyczny build jarow w chmurze

## Bez kompilowania u siebie (GitHub Actions)
1. Zaloz konto na github.com i utworz NOWE repozytorium (np. `RizzClient`).
2. Wrzuc do niego CALA zawartosc tego folderu (razem z ukrytym folderem `.github`).
   Najprosciej: "Add file -> Upload files" i przeciagnij wszystko, albo przez git.
3. Wejdz w zakladke **Actions** - build ruszy sam (ok. 3-6 min). Po sukcesie w
   **Releases** pojawia sie `rizzclient-1.21.1.jar` i `rizzclient-1.21.11.jar`.
4. Uruchom launcher i wpisz w polu "Rizz Core (GitHub)": `twojanazwa/RizzClient`.
   Launcher sam pobiera wlasciwy jar przy kazdym starcie.

(Jary mozna tez pobrac recznie z Actions -> Artifacts i wrzucic do `launcher/core/`.)

## Launcher
    cd launcher
    pip install -r requirements.txt
    python rizz_client.py

## W grze
- Prawy Shift -> menu Rizz Client
- Freelook: Lewy Alt, Zoom: C (Opcje > Sterowanie > Rizz Client)
- ESC -> logo + nick w prawym dolnym rogu

## FPS Boost (przelacznik w launcherze)
- mody: Sodium, Lithium + FerriteCore, Entity Culling, ImmediatelyFast, ModernFix, More Culling, Dynamic FPS
- options.txt: render 10, symulacja 8, szybka grafika, minimalne particle, bez VSync, bez limitu FPS,
  bez cieni encji, mniejszy biome blend (stosowane raz na wersje; Twoje nizsze wartosci zostaja)
- Java: G1GC z flagami pod niskie opoznienia, Xms = Xmx
