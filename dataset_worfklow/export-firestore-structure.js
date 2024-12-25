const admin = require('firebase-admin');
const fs = require('fs/promises');
const path = require('path');

// Initialize Firebase Admin with dev credentials
const serviceAccount = require('./dev-creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://schemessg-v3-dev.firebaseio.com"
});

const db = admin.firestore();

async function getCollectionStructure(collection, includeData = false) {
  const structure = {
    fields: {},
    collections: {}
  };

  // Get document structure from first document
  const snapshot = await collection.limit(1).get();
  if (!snapshot.empty) {
    const sampleDoc = snapshot.docs[0].data();
    for (const [key, value] of Object.entries(sampleDoc)) {
      structure.fields[key] = typeof value;
    }
  }

  // Get all documents if includeData is true
  if (includeData) {
    structure.documents = [];
    const allDocs = await collection.get();
    allDocs.forEach(doc => {
      structure.documents.push({
        id: doc.id,
        data: doc.data()
      });
    });
  }

  // Get subcollections from a sample document
  if (!snapshot.empty) {
    const sampleDocRef = snapshot.docs[0].ref;
    const subcollections = await sampleDocRef.listCollections();
    for (const subcollection of subcollections) {
      structure.collections[subcollection.id] = await getCollectionStructure(subcollection);
    }
  }

  return structure;
}

async function exportStructure() {
  try {
    const collections = await db.listCollections();
    const dbStructure = {};

    for (const collection of collections) {
      // Only include data for 'schemes' collection
      const includeData = collection.id === 'schemes';
      dbStructure[collection.id] = await getCollectionStructure(collection, includeData);
    }

    // Save to file
    const outputPath = path.join(__dirname, 'schemes-dev-firestore-structure.json');
    await fs.writeFile(
      outputPath,
      JSON.stringify(dbStructure, null, 2)
    );

    console.log(`Database structure exported to ${outputPath}`);
    process.exit(0);
  } catch (error) {
    console.error('Export failed:', error);
    process.exit(1);
  }
}

exportStructure();
