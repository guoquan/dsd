# docker

`dockerfiles` for `docker` images used by `dsd` runtime and end-user.

## dsd

Runtime image for DSD console.
DSD console will run inside a container run from this image and take control using docker API.

## jupyter

All images for end-user are designed to be based on jupter, so that user can have an interactive environment immediately.
CPU version and GPU version are provided separately.
