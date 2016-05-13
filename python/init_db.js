conn = new Mongo();
db = conn.getDB("db_dsd");
db.users.save({'Username':'user1','Password':'123','User_Type':'Admin','Max_Container_Count':3,'Max_Disk_Space':1024});
db.users.save({'Username':'user2','Password':'123','User_Type':'Common','Max_Container_Count':3,'Max_Disk_Space':1024});
