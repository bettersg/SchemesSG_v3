const admin = require('firebase-admin');
const serviceAccount = require('../dev-creds.json');

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

    // Check for missing last_llm_processed_update field
    const docsWithoutLastLlmProcessed = [];
    const docsWithoutLastScraped = [];

    snapshot.forEach(doc => {
      const data = doc.data();
      if (!data.last_llm_processed_update) {
        docsWithoutLastLlmProcessed.push(doc.id);
      }
      if (!data.last_scraped_update) {
        docsWithoutLastScraped.push(doc.id);
      }
    });

    console.log(`\nDocuments missing 'last_llm_processed_update' field: ${docsWithoutLastLlmProcessed.length}`);
    if (docsWithoutLastLlmProcessed.length > 0) {
      console.log('Document IDs missing last_llm_processed_update:');
      docsWithoutLastLlmProcessed.forEach(id => console.log(`  - ${id}`));
    }

    console.log(`\nDocuments missing 'last_scraped_update' field: ${docsWithoutLastScraped.length}`);
    if (docsWithoutLastScraped.length > 0) {
      console.log('Document IDs missing last_scraped_update:');
      docsWithoutLastScraped.forEach(id => console.log(`  - ${id}`));
    }

    // Clean up: Set scraped_text to empty string for documents without last_scraped_update
    // if (docsWithoutLastScraped.length > 0) {
    //   console.log(`\nStarting cleanup: Setting scraped_text to empty string for ${docsWithoutLastScraped.length} documents...`);

    //   const batch = db.batch();
    //   let updateCount = 0;

    //   for (const docId of docsWithoutLastScraped) {
    //     const docRef = db.collection('schemes').doc(docId);
    //     batch.update(docRef, { scraped_text: "" });
    //     updateCount++;

    //     // Firestore batch limit is 500 operations
    //     if (updateCount % 500 === 0) {
    //       console.log(`Committing batch of ${updateCount} updates...`);
    //       await batch.commit();
    //       console.log(`Committed ${updateCount} updates so far...`);
    //     }
    //   }

    //   // Commit remaining updates
    //   if (updateCount % 500 !== 0) {
    //     console.log(`Committing final batch of ${updateCount % 500} updates...`);
    //     await batch.commit();
    //   }

    //   console.log(`✅ Cleanup completed! Updated ${updateCount} documents to have empty scraped_text field.`);
    // } else {
    //   console.log('\n✅ No cleanup needed - all documents have last_scraped_update field.');
    // }

    process.exit(0); // Exit successfully
  } catch (error) {
    console.error('Error counting documents:', error);
    process.exit(1); // Exit with error
  }
}

countDocuments();
