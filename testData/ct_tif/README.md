# Segmented CT slice test images

Single-channel 8-bit TIF label images for the segmented-CT NMR workflow.
Pixel size: 4.6 μm/pixel.

| File | Phases | Pixel values |
|---|---|---|
| `solid_water_2phase.tif` | solid, water | 255 solid, 125 water |
| `solid_water_air_3phase.tif` | solid, water, air | 255 solid, 102 water, 153 air |
| `solid_water_back3phase.tif` | solid, water, background | 255 solid, 125 water, 0 outside |
| `solid_water_air_back4phase.tif` | solid, water, air, background | 255 solid, 102 water, 153 air, 0 outside |

Expected agent behaviour: the 2-value image never triggers the background
question; the 3- and 4-value images do unless the prompt states whether
background pixels exist. Used by `tests/test_ct_phase.py`.
