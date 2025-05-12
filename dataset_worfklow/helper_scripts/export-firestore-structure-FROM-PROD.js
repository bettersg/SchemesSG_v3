const admin = require('firebase-admin');
const fs = require('fs/promises');
const path = require('path');
const createObjectCsvWriter = require('csv-writer').createObjectCsvWriter;

// Initialize Firebase Admin with prod credentials
const serviceAccount = require('../prod-creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  // databaseURL: "https://schemessg-v3-dev.firebaseio.com"
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
    // Store data and headers for each collection
    const allCollectionsData = {};
    const allCollectionsHeaders = {};

    for (const collection of collections) {
      // Include data for all collections in JSON structure export
      dbStructure[collection.id] = await getCollectionStructure(collection, true);

      // Fetch all data for each collection for CSV export
      const collectionSnapshot = await collection.get();
      let collectionData = [];
      let collectionHeaders = new Set();
      collectionSnapshot.forEach(doc => {
        const data = doc.data();
        const docDataWithId = { id: doc.id, ...data };
        collectionData.push(docDataWithId);
        Object.keys(docDataWithId).forEach(key => collectionHeaders.add(key));
      });
      allCollectionsData[collection.id] = collectionData;
      allCollectionsHeaders[collection.id] = collectionHeaders;
    }

    // --- Start: JSON Structure Export ---
    const jsonOutputPath = path.join(__dirname, 'schemes-prod-firestore-structure.json');
    await fs.writeFile(
      jsonOutputPath,
      JSON.stringify(dbStructure, null, 2)
    );
    console.log(`Database structure exported to ${jsonOutputPath}`);
    // --- End: JSON Structure Export ---

    // --- Start: All Collections CSV Export ---
    for (const [collectionId, data] of Object.entries(allCollectionsData)) {
      if (data.length > 0) {
        const headersSet = allCollectionsHeaders[collectionId];
        const csvHeaders = Array.from(headersSet).map(header => ({ id: header, title: header }));
        csvHeaders.sort((a, b) => {
          if (a.id === 'id') return -1;
          if (b.id === 'id') return 1;
          return a.title.localeCompare(b.title);
        });
        const csvOutputPath = path.join(__dirname, `firestore-${collectionId}-prod.csv`);
        const csvWriter = createObjectCsvWriter({
          path: csvOutputPath,
          header: csvHeaders,
          writeHeaders: true,
        });
        const records = data.map(docData => {
          const record = {};
          csvHeaders.forEach(header => {
            record[header.id] = docData.hasOwnProperty(header.id) ? docData[header.id] : '';
            if (typeof record[header.id] === 'object' && record[header.id] !== null) {
              try {
                record[header.id] = JSON.stringify(record[header.id]);
              } catch (e) {
                console.warn(`Could not stringify field ${header.id} for doc ${docData.id}`);
                record[header.id] = '[Object]';
              }
            }
          });
          return record;
        });
        await csvWriter.writeRecords(records);
        console.log(`Collection '${collectionId}' exported to ${csvOutputPath}`);
      } else {
        console.log(`No data found in '${collectionId}' collection to export to CSV.`);
      }
    }
    // --- End: All Collections CSV Export ---

    process.exit(0);
  } catch (error) {
    console.error('Export failed:', error);
    process.exit(1);
  }
}

exportStructure();
