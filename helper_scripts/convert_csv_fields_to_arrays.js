/**
 * Converts scheme_type, what_it_gives, and who_is_it_for fields
 * from CSV strings to arrays of strings in the 'schemes' Firestore collection.
 *
 * Usage:
 *   node convert_csv_fields_to_arrays.js          # dry run (no writes)
 *   node convert_csv_fields_to_arrays.js --dev    # write to schemessg-v3-dev
 *   node convert_csv_fields_to_arrays.js --prod   # write to schemessg (production)
 *
 * Prerequisites:
 *   - dev-creds.json  (dev service account key, at repo root)
 *   - prod-creds.json (prod service account key, at repo root)
 */

const admin = require('firebase-admin');

const FIELDS_TO_CONVERT = ['scheme_type', 'what_it_gives', 'who_is_it_for'];
const BATCH_SIZE = 400; // Firestore batch limit is 500; keep headroom

const args = process.argv.slice(2);
const isDev = args.includes('--dev');
const isProd = args.includes('--prod');
const isDryRun = !isDev && !isProd;

if (isDryRun) {
  console.log('DRY RUN — no writes will be made. Pass --dev or --prod to apply changes.');
}

const credsFile = isProd ? '../prod-creds.json' : '../dev-creds.json';
const projectId = isProd ? 'schemessg' : 'schemessg-v3-dev';

let serviceAccount;
try {
  serviceAccount = require(credsFile);
} catch (e) {
  console.error(`Could not load credentials from ${credsFile}:`, e.message);
  process.exit(1);
}

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: `https://${projectId}.firebaseio.com`,
});

const db = admin.firestore();

/**
 * Convert a CSV string to a trimmed array of strings.
 * Returns null (skip) if the value is already an array or empty.
 */
function csvToArray(value) {
  if (Array.isArray(value)) return null; // already correct, skip
  if (typeof value !== 'string' || !value.trim()) return []; // empty/null → empty array
  return value.split(',').map(v => v.trim()).filter(v => v.length > 0);
}

async function migrate() {
  const collectionRef = db.collection('schemes');
  const snapshot = await collectionRef.get();

  console.log(`Found ${snapshot.size} documents in 'schemes' collection.`);

  let toUpdate = [];
  let alreadyArrayCount = 0;

  snapshot.forEach(doc => {
    const data = doc.data();
    const updates = {};

    for (const field of FIELDS_TO_CONVERT) {
      const value = data[field];
      if (Array.isArray(value)) {
        alreadyArrayCount++;
        continue;
      }
      const converted = csvToArray(value);
      if (converted !== null) {
        updates[field] = converted;
      }
    }

    if (Object.keys(updates).length > 0) {
      toUpdate.push({ ref: doc.ref, id: doc.id, updates });
    }
  });

  console.log(`Documents already using arrays (skipped): ${alreadyArrayCount}`);
  console.log(`Documents to update: ${toUpdate.length}`);

  if (isDryRun) {
    console.log('\nSample of planned updates (first 5):');
    toUpdate.slice(0, 5).forEach(({ id, updates }) => {
      console.log(`  ${id}:`, JSON.stringify(updates));
    });
    console.log('\nRe-run with --dev or --prod to apply.');
    process.exit(0);
  }

  // Write in batches
  let updatedCount = 0;
  for (let i = 0; i < toUpdate.length; i += BATCH_SIZE) {
    const chunk = toUpdate.slice(i, i + BATCH_SIZE);
    const batch = db.batch();
    chunk.forEach(({ ref, updates }) => batch.update(ref, updates));
    await batch.commit();
    updatedCount += chunk.length;
    console.log(`  Committed batch: ${updatedCount}/${toUpdate.length}`);
  }

  console.log(`\nDone. Updated ${updatedCount} documents in '${projectId}'.`);
  process.exit(0);
}

migrate().catch(err => {
  console.error('Migration failed:', err);
  process.exit(1);
});
