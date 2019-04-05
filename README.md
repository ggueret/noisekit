noisekit
========

**Work in progress, anything can be broken without any warranty.**


Usage
-----

Run the mitigator to listen for noise and reply with a 20 Hz square frequency when the threshold of 300 RMS is reached.

```
noisekit mitigate -low 300 -lt 'square:20hz,5s'
```

The `-low` and `-lt` arguments means threshold and tone sound to reply for `low` level.
Actually, the noise can be qualified by the `low`, `medium` or `high` levels. Which allow to reply differently according the context.

Reply with some funny sounds using the default thresholds :

```
noisekit mitigate -ls godzilla_roar.mp3 -ms zombie.mp3 -hs napalm_death_you_suffer.mp3
```

Reply with multiple sounds, in a cycle fashion.

```
noisekit mitigate -ls acdc_p1.mp3 -ls acdc_p2.mp3 -ls acdc_p3.mp3 -ls acdc_p4.mp3 --picker=cycle
```

Visualize ambiant noise from a console, useful to target good thresholds to use with the mitigator.

```
noisekit visualize
```
