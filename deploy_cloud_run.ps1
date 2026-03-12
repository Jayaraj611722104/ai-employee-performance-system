param(
  [string]$ProjectId = "your-gcp-project-id",
  [string]$Region = "us-central1",
  [string]$Service = "pulsehr-api",
  [string]$MySQLHost = "localhost",
  [string]$MySQLPort = "3306",
  [string]$MySQLUser = "root",
  [string]$MySQLPassword = "Root12345",
  [string]$MySQLDb = "pulsehr"
)
gcloud config set project $ProjectId
gcloud run deploy $Service --source . --region $Region --allow-unauthenticated --set-env-vars "PORT=8080,MYSQL_HOST=$MySQLHost,MYSQL_PORT=$MySQLPort,MYSQL_USER=$MySQLUser,MYSQL_PASSWORD=$MySQLPassword,MYSQL_DB=$MySQLDb"
