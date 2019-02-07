README.md

#TODO:

If you want to have the OTP as a separate field then we'll also need to change POST part of the login_page function in https://bitbucket.org/oruebel/openmsi/src/master/omsi_server/omsi_client/views.py to append the OTP to password before authenticating. This should be pretty simple too,

#Useful commands:

```bash
docker build  -t registry.spin.nersc.gov/bpb20/openmsi_web:20190104.1 .
docker run -p 8000:8000 -i --rm -t registry.spin.nersc.gov/bpb20/openmsi_web:20190104.1 /bin/bash
docker login registry.spin.nersc.gov
docker push registry.spin.nersc.gov/bpb20/openmsi_web:20190104.1
```

In the interactive Docker process I did these two commands:

```bash
python manage.py syncdb
python manage.py runserver 0.0.0.0:8000
```

From browser do:
localhost:8000

Note that copy to clipboard doesn't work from inside docker interactive.