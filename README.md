# Viridiana Álvarez: exposé d'espagnol en motion design

- 🎬 **La vidéo :** [`video/viridiana_alvarez.mp4`](video/viridiana_alvarez.mp4) (1920×1080, 2 min 12, avec musique)
- 🗣️ **Le texte à dire à l'oral :** [`TEXTE_ORAL.md`](TEXTE_ORAL.md) (espagnol + traduction + vocabulaire)

Vidéo d'origine : [Canal Once, « Conoce a Viridiana Álvarez, alpinista mexicana »](https://youtube.com/shorts/Ut4xmapOcGk)

## Comment c'est fabriqué
L'animation est entièrement codée (HTML/CSS/JS) dans `video/index.html` : chaque image est calculée à partir du temps `t`.
- `video/render.mjs` capture les images avec Playwright (Chromium) et les encode avec ffmpeg
- `video/audio.py` génère la musique et les effets sonores, synchronisés avec les transitions

```bash
cd video
node render.mjs silent.mp4                 # images → vidéo
python3 audio.py soundtrack.wav            # bande-son
ffmpeg -i silent.mp4 -i soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest viridiana_alvarez.mp4
```
Pour un aperçu en direct, ouvre `video/index.html` dans un navigateur.
