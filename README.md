# Viridiana Álvarez: exposé d'espagnol en motion design

- 🎬 **La vidéo :** [`video/viridiana_alvarez.mp4`](video/viridiana_alvarez.mp4) (1920×1080, 2 min 25, style « site web 3D » cinématique)
- 🗣️ **Le texte à dire à l'oral :** [`TEXTE_ORAL.md`](TEXTE_ORAL.md) (espagnol + traduction + vocabulaire)

Vidéo d'origine : [Canal Once, « Conoce a Viridiana Álvarez, alpinista mexicana »](https://youtube.com/shorts/Ut4xmapOcGk)

## Comment c'est fabriqué
L'animation est entièrement codée (HTML/CSS/JS) dans `video/index.html` : chaque image est calculée à partir du temps `t`.
- `video/render.mjs` capture les images avec Playwright (Chromium) et les encode avec ffmpeg
- `video/audio_v2.py` mixe la musique (« Volatile Reaction », Kevin MacLeod, incompetech.com, CC BY 4.0) avec des whoosh/impacts calés sur les transitions (grille à 155 BPM)
- `video/make_clouds.py` génère les nuages traversés par la caméra
- Photos : Pexels (licence libre) · Images du reportage : Canal Once
- Première version (plus simple) : `video/index_v1.html`

```bash
cd video
node render.mjs silent.mp4                 # images → vidéo
python3 audio_v2.py music/volatile_reaction.mp3 soundtrack.wav   # bande-son
ffmpeg -i silent.mp4 -i soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest viridiana_alvarez.mp4
```
Pour un aperçu en direct, ouvre `video/index.html` dans un navigateur.
