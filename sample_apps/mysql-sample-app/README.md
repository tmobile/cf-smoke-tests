# mysql-example-app
This is a simple app to check mysql service availability on PCF foundations.

## Getting started
```
$ git clone git@<git-url>/mysql-sample-app.git

$ cd mysql-example-app

$ cf login -a {foundation}

$ cf target -o {org} -s {space}

$ cf create-service p-mysql {plan} {mysql_service_instance_name}

$ cf push --no-start

$ cf bind-service mysql-example-app {mysql_service_instance_name}

$ cf start mysql-example-app

$ curl -X GET "{app_url}"

$ curl -X GET "{app_url}/user"

$ curl -X GET "{app_url}/users"

$ curl -X POST "{app_url}/user"

$ curl -X PUT "{app_url}/user?id={id}&name=test_user&email=test_user@test_domain.com"

$ curl -X DELETE "{app_url}/user?id={id}"

$ cf unbind-service mysql-example-app {mysql_service_instance_name}

$ cf delete-service {mysql_service_instance_name}

$ cf delete mysql-example-app
```

## REST Endpoints
- `/`: Home page.
- `/user`:
   `GET`: Return the first user in the database.
   `POST`: Add a user.
   `PUT`: Update a user.
   `DELETE`: Delete a user.
- `/users`: 
   `GET`: Return all the users in the database.
