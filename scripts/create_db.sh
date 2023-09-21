docker run -itd --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=P@ssw0rd mysql

docker run --name mongo -v /mymongo/data:/data/db -p 27017:27017 --privileged=true -d mongo