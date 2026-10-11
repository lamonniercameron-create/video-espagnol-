# Viridiana Álvarez: exposé d'espagnol en motion design

- 🎬 **La vidéo :** [`video/viridiana_alvarez.mp4`](video/viridiana_alvarez.mp4) (1920×1080, 2 min 25, style « site web 3D » cinématique)
- 🗣️ **Le texte à dire à l'oral :** [`TEXTE_ORAL.md`](TEXTE_ORAL.md) (espagnol + traduction + vocabulaire)

Vidéo d'origine : [Canal Once, « Conoce a Viridiana Álvarez, alpinista mexicana »](https://youtube.com/shorts/Ut4xmapOcGk)

## Comment c'est fabriqué
L'animation est entièrement codée (HTML/CSS/JS) dans `video/index.html` : chaque image est calculée à partir du temps `t`.
- `video/render.mjs` capture les images avec Playwright (Chromium) et les encode avec ffmpeg
- `video/audio_v4.py` : bande-son finale, « Caliente » (Inna) en entier, d’un seul tenant du début à la fin (source non versionnée)
- `video/audio_v3.py` (ancien montage) remonte la chanson choisie (« Caliente », Inna ; extrait TikTok raccordé à l’extrait public Deezer de 30 s pour obtenir 77 s d’un seul tenant) (130 BPM, extraite de la vidéo TikTok fournie, non versionnée : `video/music/chanson.wav`) sur sa grille de mesures : intro allongée pour que le drop tombe à 0:30, puis relancé sur « PRIMERA MUJER » (1:31) ; + whoosh/impacts sur les transitions
- `video/audio_v2.py` : ancienne bande-son (« Volatile Reaction », Kevin MacLeod, CC BY 4.0)
- `video/make_clouds.py` génère les nuages traversés par la caméra
- Photos : Pexels (licence libre) · Images du reportage : Canal Once
- Première version (plus simple) : `video/index_v1.html`

```bash
cd video
node render.mjs silent.mp4                 # images → vidéo
python3 audio_v3.py music/chanson.wav soundtrack.wav   # bande-son
ffmpeg -i silent.mp4 -i soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest viridiana_alvarez.mp4
```
Pour un aperçu en direct, ouvre `video/index.html` dans un navigateur.
