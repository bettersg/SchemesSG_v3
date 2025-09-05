const admin = require('firebase-admin');
const { FieldValue } = require('firebase-admin/firestore');
const serviceAccount = require('../dev-creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://schemessg-v3-dev.firebaseio.com"
});

const db = admin.firestore();

async function removeField(fieldName) {
  try {
    const snapshot = await db.collection('schemes').get();
    const batch = db.batch();

    snapshot.forEach(doc => {
      batch.update(doc.ref, { [fieldName]: FieldValue.delete() });
    });

    await batch.commit();
    console.log(`Successfully removed field '${fieldName}' from ${snapshot.size} documents.`);
    process.exit(0);
  } catch (error) {
    console.error(`Error removing field '${fieldName}':`, error);
    process.exit(1);
  }
}

removeField("last_modified_date");
