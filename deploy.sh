git pull origin master

docker build -t rsmnextgenwebsite.azurecr.io/nextgen:v1 .

az acr login --name rsmnextgenwebsite

docker push rsmnextgenwebsite.azurecr.io/nextgen:v1
