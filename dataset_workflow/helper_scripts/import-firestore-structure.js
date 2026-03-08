const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

// Initialize Firebase Admin with prod credentials
const serviceAccount = require('../prod-creds.json');
// const serviceAccount = require('../dev-creds.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

// Get Firestore instance
const db = admin.firestore();
db.settings({
  ignoreUndefinedProperties: true,
  timestampsInSnapshots: true,
});

// Collections to import: name, CSV file, and fields that need JSON.parse()
const COLLECTIONS = [
  {
    collectionName: 'schemes',
    csvFile: 'firestore-schemes-prod.csv',
    jsonFields: [],
  },
  {
    collectionName: 'chatHistory',
    csvFile: 'firestore-chatHistory-prod.csv',
    jsonFields: ['messages', 'metadata', 'versions'],
  },
  {
    collectionName: 'schemeEntries',
    csvFile: 'firestore-schemeEntries-prod.csv',
    jsonFields: [],
  },
  {
    collectionName: 'schemes_embeddings',
    csvFile: 'firestore-schemes_embeddings-prod.csv',
    jsonFields: ['embedding'],
  },
  {
    collectionName: 'userFeedback',
    csvFile: 'firestore-userFeedback-prod.csv',
    jsonFields: [],
  },
  {
    collectionName: 'userQuery',
    csvFile: 'firestore-userQuery-prod.csv',
    jsonFields: ['schemes_response'],
  },
];

function parseField(value, isJson) {
  if (!isJson || !value) return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function readCsv(filePath) {
  return new Promise((resolve, reject) => {
    const rows = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => rows.push(row))
      .on('end', () => resolve(rows))
      .on('error', (err) => reject(err));
  });
}

async function importCollection({ collectionName, csvFile, jsonFields }) {
  console.log(`\n--- Collection: ${collectionName} ---`);

  // Existence check
  const countSnap = await db.collection(collectionName).count().get();
  const existingCount = countSnap.data().count;
  if (existingCount > 0) {
    console.log(`  ${existingCount} documents found, skipping import.`);
    return;
  }
  console.log(`  Collection empty, proceeding with import.`);

  const filePath = path.join(__dirname, csvFile);
  const rows = await readCsv(filePath);
  console.log(`  Read ${rows.length} rows from ${csvFile}`);

  const jsonFieldSet = new Set(jsonFields);
  let batch = db.batch();
  let batchCount = 0;
  let totalImported = 0;

  for (const row of rows) {
    const { id, ...fields } = row;
    if (!id) {
      console.warn(`  Skipping row with missing id: ${JSON.stringify(row).slice(0, 80)}`);
      continue;
    }

    const data = {};
    for (const [key, value] of Object.entries(fields)) {
      data[key] = parseField(value, jsonFieldSet.has(key));
    }

    const ref = db.collection(collectionName).doc(id);
    batch.set(ref, data);
    batchCount++;
    totalImported++;

    if (batchCount === 500) {
      await batch.commit();
      console.log(`  Committed batch of 500 (total so far: ${totalImported})`);
      batch = db.batch();
      batchCount = 0;
    }
  }

  if (batchCount > 0) {
    await batch.commit();
    console.log(`  Committed final batch of ${batchCount}`);
  }

  console.log(`  Done. Imported ${totalImported} documents into '${collectionName}'.`);
}

async function importAllCollections() {
  console.log('Starting production Firestore import...');
  console.log('NOTE: Ensure the Firestore database has been re-enabled before running this script.\n');

  for (const config of COLLECTIONS) {
    try {
      await importCollection(config);
    } catch (err) {
      console.error(`  ERROR importing '${config.collectionName}':`, err);
      process.exit(1);
    }
  }

  console.log('\nAll collections imported successfully.');
  process.exit(0);
}

importAllCollections();
