## Example docker-compose configuration

Hello and thank you for giving Kaplan Cloud a try!

This example configuration assumes that you have [nginxproxy/nginx-proxy](https://hub.docker.com/r/nginxproxy/nginx-proxy) running on the same machine and connected to a docker network the name of which you will declare under NETWORK_NAME in the .env file. Below is an example .env file:

    POSTGRES_DB=postgres
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_HOST=db
    VIRTUAL_HOST=deneme.com.tr
    NETWORK_NAME=deneme

You should modify all fields except for POSTGRES_HOST.

When you're done, all that is left to do is to run `docker-compose up -d` while in the same directory as docker-compose.yml

### Links
1. [Kaplan Cloud docker repository](https://hub.docker.com/r/kaplanpro/cloud)
2. [Kaplan homepage](https://kaplan.pro)
