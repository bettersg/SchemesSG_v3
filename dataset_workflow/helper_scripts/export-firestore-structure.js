const admin = require('firebase-admin');
const fs = require('fs/promises');
const path = require('path');
const createObjectCsvWriter = require('csv-writer').createObjectCsvWriter;

// Initialize Firebase Admin with dev credentials
const serviceAccount = require('../dev-creds.json');

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
    let schemesData = [];
    let schemeHeaders = new Set(); // Use a Set to automatically handle unique headers

    for (const collection of collections) {
      // Only include data for 'schemes' collection in JSON structure export
      const includeJsonData = collection.id === 'schemes';
      dbStructure[collection.id] = await getCollectionStructure(collection, includeJsonData);

      // Separately fetch all data for 'schemes' collection for CSV export
      if (collection.id === 'schemes') {
        const schemesSnapshot = await collection.get();
        schemesSnapshot.forEach(doc => {
          const data = doc.data();
          // Add document id to the data
          const docDataWithId = { id: doc.id, ...data };
          schemesData.push(docDataWithId);
          // Collect all unique field names for headers
          Object.keys(docDataWithId).forEach(key => schemeHeaders.add(key));
        });
      }
    }

    // --- Start: JSON Structure Export ---
    // Save JSON structure to file
    const jsonOutputPath = path.join(__dirname, 'schemes-dev-firestore-structure.json');
    await fs.writeFile(
      jsonOutputPath,
      JSON.stringify(dbStructure, null, 2)
    );
    console.log(`Database structure exported to ${jsonOutputPath}`);
    // --- End: JSON Structure Export ---

    // --- Start: Schemes CSV Export ---
    if (schemesData.length > 0) {
      // Convert Set of headers to the format required by csv-writer
      const csvHeaders = Array.from(schemeHeaders).map(header => ({ id: header, title: header }));
      // Ensure 'id' column is first if present
      csvHeaders.sort((a, b) => {
        if (a.id === 'id') return -1;
        if (b.id === 'id') return 1;
        return a.title.localeCompare(b.title); // Alphabetical sort for others
      });


      const csvOutputPath = path.join(__dirname, 'firestore-schemes-dev.csv');
      const csvWriter = createObjectCsvWriter({
        path: csvOutputPath,
        header: csvHeaders,
        // Ensure all fields are written, even if missing in some docs (will write empty string)
        writeHeaders: true,
      });

      // Prepare records, ensuring all headers exist for each record
      const records = schemesData.map(docData => {
         const record = {};
         csvHeaders.forEach(header => {
            record[header.id] = docData.hasOwnProperty(header.id) ? docData[header.id] : '';
             // Handle potential objects/arrays by stringifying them for CSV
            if (typeof record[header.id] === 'object' && record[header.id] !== null) {
                try {
                    record[header.id] = JSON.stringify(record[header.id]);
                } catch (e) {
                    console.warn(`Could not stringify field ${header.id} for doc ${docData.id}`);
                    record[header.id] = '[Object]'; // Placeholder for unstringifiable objects
                }
            }
         });
         return record;
      });


      await csvWriter.writeRecords(records);
      console.log(`Schemes collection exported to ${csvOutputPath}`);
    } else {
       console.log("No data found in 'schemes' collection to export to CSV.");
    }
    // --- End: Schemes CSV Export ---

    process.exit(0);
  } catch (error) {
    console.error('Export failed:', error);
    process.exit(1);
  }
}

exportStructure();
