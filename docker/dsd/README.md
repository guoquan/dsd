# DSD console

Use the Ubuntu 14:04 base image for minimum dependency.
Libraries are install according to requirement of the system:
* Nginx: front-end web server
* Python: we are python driven
* Flask: web-container
* MongoDB: NoSQL database

Don't have to use different container for different service now.

# How to

```bash
sudo docker run --rm -it --name dsd-console \
    -p 10080:80 -p 15000:5000 \
    -v ~/workspace-dsd-console:/root/workspace \
    -v ~/workspace-dsd-console-etc/etc/nginx/conf.d:/etc/nginx/conf.d \
    dsd-console
```

Use 10080 for nginx and 15000 for flask. MongoDB is not exported.
Use `--rm` to keep it clean after running.
