#POS system to BarberShop

This code is about a simple pos system to register sels for products and services, it can control the inventory, profits and some taxes.

- Backend: Python-Django
- Frontend AdminLte/Javascript
- DB Sqlite3 - Some SQL querys on views for temporal tables

How to run: 
1. just clon the repository 
2. build docker image, run "docker build -t "yourtag" . "
3. run the image "docker run -p "port":80 -t "yourtag" "
4. go to localhost:"port"

replace "port" to wherever number you want
and "tag" to wherever tag you want

here you can find a live example: http://3.92.185.70:81/ 

Credentials:
- user: administrator
- pass: admin123456
