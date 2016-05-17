# docker

`dockerfiles` for `docker` images used by `dsd` runtime and end-user.
We also use the public registry on [docker hub](http://hub.docker.com).
Our images are available as under [dsdgroup](https://hub.docker.com/u/dsdgroup/).

You can also build images locally using `build-local-images.sh`.
```bash
chmod u+x build-local-images.sh
./build-local-images.sh
```

## dsd

Runtime image for DSD console.
DSD console will run inside a container run from this image and take control using docker API.

## jupyter

All images for end-user are designed to be based on jupter, so that user can have an interactive environment immediately.
CPU version and GPU version are provided separately.
