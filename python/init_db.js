conn = new Mongo();
db = conn.getDB('dsd');

// add default dsd system congfiguration
db.config.save({
  docker_url: 'unix:///var/run/docker.sock',
  nvd_url: 'http://localhost:3476',
  default_max_container: 3,
  default_max_disk: 1024
});

// add some init users
db.users.save({
  username: 'User1',
  password: '123',
  type : 0 // 0 for administrator
});
db.users.save({
  username: 'User2',
  password: '123',
  type: 1, // 1 for plain user
  max_container: 3,
  max_disk: 1024
});
