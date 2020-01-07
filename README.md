# FeelYourMusic: 🎧  
`Personalized Spotify playlists based on feelings`

Background:

1. Creo una base de datos con más de 3000 canciones de 48 playlists distintas de Spotify.
2. A cada canción le cargo todos los parámetros internos que te ofrece la API de Spotify (danceability, valence, energy, tempo, loudness, key …).
3. Con el fin de seleccionar con cuáles me quedo, realizo varios análisis y selecciono  `Energy`, cuánto de intensa y activa es la canción, `Valence`,  cómo de positiva es la canción y `Danceability`,  como de ‘bailable’ es la canción.
4. Escalo y normalizo los datos.
5. Como el objetivo es agrupar las canciones por sentimientos y estas a priori no están clasificadas elijo como **método de aprendizaje no supervisada** la aplicación del **algoritmo k-medias**, que agrupa objetos en k grupos basándose en sus características.
6. El número óptimo de k lo determino usando la técnica del codo y obtengo 6.
7. Una vez etiquetados las más de 3000 canciones, aplico sobre estas un **modelo de aprendizaje supervisado**, entreno  clasificador del centroide más cercano que me permitirá clasificar/etiquetar las canciones de los usuarios que usen la app.++

### Ejemplo clasificación 

![Ejemplo](/images/ejemplo.png)

### Flujo aplicación 

![Ejemplo](/images/flow.png)
