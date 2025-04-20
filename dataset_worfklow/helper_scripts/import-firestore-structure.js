const admin = require('firebase-admin');
const fs = require('fs/promises');
const path = require('path');

// Initialize Firebase Admin with prod credentials
// const serviceAccount = require('./prod-creds.json');
const serviceAccount = require('../dev-creds.json')
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

// Get Firestore instance with specific database
const db = admin.firestore();
db.settings({
  ignoreUndefinedProperties: true,
  timestampsInSnapshots: true,
  // databaseId: 'schemes-prod'  // Specify the database ID here
});

async function createEmptyCollection(collectionName, fields) {
  try {
    console.log(`Creating collection: ${collectionName}`);

    // Create a document with the field structure
    const tempDoc = {};
    for (const [field, type] of Object.entries(fields)) {
      switch(type) {
        case 'string':
          tempDoc[field] = '';
          break;
        case 'object':
          tempDoc[field] = {};
          break;
        default:
          tempDoc[field] = null;
      }
    }

    // Add a sample document
    await db.collection(collectionName).add(tempDoc);
    console.log(`Successfully initialized collection: ${collectionName}`);
  } catch (error) {
    console.error(`Error creating collection ${collectionName}:`, error);
    throw error;
  }
}

async function importStructure() {
  try {
    console.log('Starting import...');
    const structurePath = path.join(__dirname, 'schemes-dev-firestore-structure.json');
    const structure = JSON.parse(
      await fs.readFile(structurePath, 'utf8')
    );

    // Import schemes data first
    if (structure.schemes?.documents) {
      console.log(`Found ${structure.schemes.documents.length} schemes to import`);

      let batch = db.batch();
      let count = 0;
      let batchCount = 0;

      for (const doc of structure.schemes.documents) {
        const ref = db.collection('schemes').doc(doc.id);
        batch.set(ref, doc.data);
        count++;

        if (count === 500) {
          try {
            await batch.commit();
            console.log(`Committed batch ${++batchCount} (500 documents)`);
            batch = db.batch();
            count = 0;
          } catch (error) {
            console.error(`Error committing batch ${batchCount}:`, error);
            throw error;
          }
        }
      }

      if (count > 0) {
        try {
          await batch.commit();
          console.log(`Committed final batch of ${count} documents`);
        } catch (error) {
          console.error('Error committing final batch:', error);
          throw error;
        }
      }
    }

    // Create other collections
    for (const [collectionName, collectionData] of Object.entries(structure)) {
      if (collectionName !== 'schemes') {
        await createEmptyCollection(collectionName, collectionData.fields);
      }
    }

    console.log('Import completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('Import failed:', error);
    process.exit(1);
  }
}

importStructure();
