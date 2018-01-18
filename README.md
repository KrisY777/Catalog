# Project: Linux Server
## Author:  Kristina Yakunina
To run the project:
1. Log in to your Linux terminal
2. Run command ssh -i Linux-Server.pem grader@ec2-18-221-221-23.us-east-2.compute.amazonaws.com
where Linux-Server.pem is a public key, which is located in the same folder, as Read_Me file.
3. When logged in, navigate to the root folder and then use command cd var/www/catalog/Catalog/item_catalog   
4. After this use command sudo python ItemsCatalog.py
5. Password for sudo command is  grader
6. Open http://0.0.0.0:5000/ on your web browser. Done


