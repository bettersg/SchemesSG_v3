const admin = require('firebase-admin');
const serviceAccount = require('./creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://schemessg-v3-dev.firebaseio.com"
});

const db = admin.firestore();

async function countDocuments() {
  try {
    const snapshot = await db.collection('schemes').get();
    const count = snapshot.size;
    console.log(`Number of documents in 'schemes' collection: ${count}`);
    process.exit(0); // Exit successfully
  } catch (error) {
    console.error('Error counting documents:', error);
    process.exit(1); // Exit with error
  }
}

countDocuments();
