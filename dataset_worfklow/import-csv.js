
const fs = require('fs');
const csv = require('csv-parser');
const admin = require('firebase-admin');
const serviceAccount = require('./dev-creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://schemessg-v3-dev.firebaseio.com"
});

// Reference to Firestore
const db = admin.firestore();

// Function to clear a collection
async function clearCollection(collectionRef) {
  const snapshot = await collectionRef.get();
  const batchSize = snapshot.size;

  if (batchSize === 0) {
    return;
  }

  const batch = db.batch();
  snapshot.docs.forEach(doc => {
    batch.delete(doc.ref);
  });

  await batch.commit();
  console.log(`Cleared ${batchSize} documents from the collection.`);
}

// Function to import CSV
async function importCSV(filePath) {
  const collectionRef = db.collection('schemes');

  // Clear the collection first
  await clearCollection(collectionRef);

  const rows = [];
  let hasError = false;

  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => {
        rows.push(row); // Keep track of rows processed
        if (hasError) return; // Skip further rows if an error occurred

        collectionRef.add(row).catch(error => {
          console.error('Error adding document:', row, error);
          hasError = true; // Flag error
          reject(new Error(`Processing stopped due to error with row: ${JSON.stringify(row)}. Error: ${error.message}`));
        });
      })
      .on('end', () => {
        if (!hasError) {
          console.log('CSV file successfully processed');
          resolve();
        }
      })
      .on('error', (error) => {
        console.error('Error reading CSV file:', error);
        reject(error); // Pass error to promise
      });
  });
}

// Change 'path/to/your-file.csv' to your actual CSV file path
const csvFilePath = 'schemes 11 nov.csv';
importCSV(csvFilePath)
  .then(() => console.log('Import completed successfully'))
  .catch((error) => {
    console.error('Import failed:', error.message);
    process.exit(1); // Stop the process due to failure
  });
