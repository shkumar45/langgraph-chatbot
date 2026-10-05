# Commands for understanding
docker network create chatbot 2>/dev/null

docker run -d --name api --network chatbot -p 8000:8000 --env-file .env skumar45/langgraph-chatbot-backend
docker run -d --name ui  --network chatbot -p 3000:3000 skumar45/langgraph-chatbot-frontend