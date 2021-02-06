# OpenMSI
The software behind the mass spec portal at [openmsi.nersc.gov](https://openmsi.nersc.gov/).


## Deployment Instructions
1. Install [docker](https://docs.docker.com/get-docker/) or [podman](https://podman.io/getting-started/installation) on your local machine.
1. Git clone this repo to your local machine:
  - `git clone https://github.com/biorack/openmsi_web`
2. Build and push images to [registry.spin.nersc.gov](https://registry.spin.nersc.gov):
  - `./openmsi_web/build.sh`
3. Git clone this repo to a cori login node:
  - `git clone https://github.com/biorack/openmsi_web`
4. In the root directory of the openmsi_web repo, create the following files containing your TLS private key and certificate ((w/ issuer after, PEM encoded):
  - .tls.key
  - .tls.cert
5. Ensure the .tls.key file is only readable by you:
  - `chmod 600 .tls.key
6. Run the deployment script: `./deploy.sh`
  - You'll need to pass it flags the location of the openmsi docker images on the repo.
