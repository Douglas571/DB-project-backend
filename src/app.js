require('dotenv').config()

const express = require('express')
const cors = require('cors')
const jwt = require('jsonwebtoken');
const mariadb = require('mariadb');

const Prisma = require('@prisma/client')
const prisma = new Prisma.PrismaClient()

const app = express();

const JWT_SECRET_KEY = 'your_secret_key';

// Apply middlware for CORS and JSON endpoing
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/', (req, res) => {
  res.send('Hello World!');
});

// TODO: add the routers to regist and get the token
// TODO: integrate the data base

// create a connection with the database


async function createUser() {

}


async function main() {
  // THE DATA BASE INITIALIZATION
  // create the use table
  const conn = await mariadb.createConnection({
    host: 'localhost',
    port: '3308',
    user: 'root',
    password: '',
    // database: 'appdb'
  })

  let res

  try {
    res = await conn.query('create database appdb')    
  } catch(err) {
    console.log(err)
  }

  res = await conn.query('use appdb')

  res = await conn.query('show databases')
  console.log({res})

  async function createUsersTable() {
    let res 
    
    try {
      res = await conn.query(`
      CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        username VARCHAR(50) NOT NULL, password VARCHAR(255) NOT NULL, 
        birth_date DATE, weight_kg DECIMAL(5, 2), height_cm DECIMAL(5, 2));`)
      console.log(res)
    } catch(err) {
      if (err.errno === 1050) {
        console.log('the table already exists n.n')
      }
    }

    return res
  }

  // designe a query to save user
  async function saveUser(newUser) {
    // let query_1 = `INSERT INTO users (username, password`
    // let query_2 = ` VALUES ('${newUser.username}', '${newUser.password}'`
    // if (newUser.birth_date) {
    //   query_1 += `, birth_date`
    //   query_2+= `, '${newUser.birth_date}'`
    // }
    // if (newUser.weight_kg) {
    //   query_1 += `, weight_kg`
    //   query_2 += `, '${newUser.weight_kg}'`
    // }
    // if (newUser.height_cm) {
    //   query_1 += `, height_cm`
    //   query_2 += `, '${newUser.height_cm}'`
    // }

    // query_1 += ')'
    // query_2 += ')'

    // let query = query_1 + query_2 

    // const res = await conn.query(query)

    // const resUser = await conn.query(`SELECT * FROM users WHERE username='${newUser.username}'`)
    // const user = resUser[0] // TODO: make the username unique and delete the array signature.
    
    // return { user }
    let res = await prisma.users.create({
      data: newUser
    })

    return res
  }

  const randomUser = {
    username: 'randomuser' + Date.now(),
    password: '123456789doiglas'
  }
  
  async function getUser(username) {
    const res = await conn.query(`SELECT * FROM users WHERE username='${username}'`)
    
    return res[0]
  }

  async function deleteUser(username) {
    const res = conn.query(`DELETE FROM users WHERE username = '${username}'`)
    return res
  }

  let result = await createUsersTable()

  let admin = await getUser('admin')
  if (!admin) {
    await saveUser({username: 'admin', password: 'admin', birth_date: '2024-01-02'})
  }


  // some random tests :v
  result = await saveUser(randomUser)
  console.log(result)

  let user = await getUser(randomUser.username)
  console.log(user)

  // result = await deleteUser(randomUser.username)
  // console.log(res)



  // THE APP INITIALIZATION

  // Example user data (replace this with your user authentication logic)
  const users = [
    {
      id: 1,
      username: 'benjamin',
      password: '1234567890'
    }
  ];

  app.get('/test', async (req, res) => {
    let results = await prisma.users.findMany()
    console.log({results})
    res.json({msg: "Hello tester!"})
  })

  // Register route - simulate user registration
  app.post('/singup', (req, res) => {

    if (!req.body.username || !req.body.password) {
      return res.json({msg: 'Error: you need to provide username and password'})
    }
    
    const newUser = {
      username: req.body.username,
      password: req.body.password
    };

    console.log(newUser)

    // Add your validation and user creation logic here
    saveUser(newUser)
      .then( result => {

        console.log({result})
        res.status(200)
        res.json({ 
          msg: 'User registered successfully',
          user: result.user,
          token: jwt.sign({ userId: result?.user?.id }, JWT_SECRET_KEY, { expiresIn: '1h' })
        });
      })
  })

  // Login route - generate JWT token upon successful login
  app.post('/login', (req, res) => {
    const { username, password } = req.body;

    // Simulating user authentication - you should use your actual authentication logic here
    getUser(username)
      .then( user => {

        console.log({user})
        if (!user || user.password !== password) {
          return res.status(401).json({ message: 'Invalid username or password' });
        }
        
        const token = jwt.sign({ userId: user.id }, JWT_SECRET_KEY, { expiresIn: '1h' });
    
        res.json({ token });
      })
  });

  // Protected route - access with a valid JWT token
  app.get('/protected', authenticateToken, (req, res) => {
    res.json({ message: 'Access granted to protected route' });
  });

  // Middleware to verify JWT token
  function authenticateToken(req, res, next) {
    const token = req.headers['authorization'];

    if (token) {
      jwt.verify(token, JWT_SECRET_KEY, (err, decoded) => {
        if (err) {
          return res.status(403).json({ message: 'Token is not valid' });
        }
        req.userId = decoded.userId;
        next();
      });
    } else {
      res.status(401).json({ message: 'Unauthorized - Token not provided' });
    }
  }

  app.listen(process.env.PORT, () =>
    console.log(`Server running on port ${process.env.PORT}!`),
  );


}

main()