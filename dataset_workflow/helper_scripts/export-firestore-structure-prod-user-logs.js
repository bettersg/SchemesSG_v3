const admin = require('firebase-admin');
const fs = require('fs/promises');
const path = require('path');
const createObjectCsvWriter = require('csv-writer').createObjectCsvWriter;

// Initialize Firebase Admin with dev credentials
const serviceAccount = require('../prod-creds.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
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

async function exportCollections() {
  try {
    const userQuerySnapshot = await db.collection('userQuery').get();
    const chatHistorySnapshot = await db.collection('chatHistory').get();

    // Create a map to store merged data
    const mergedData = new Map();

    // Process userQuery documents
    userQuerySnapshot.forEach(doc => {
      const data = doc.data();

      // Extract only Scheme and scheme_id from schemes_response
      let schemesResponseString = '';
      if (data.schemes_response) {
        try {
          // Handle both array and single object cases
          const schemeArray = Array.isArray(data.schemes_response)
            ? data.schemes_response
            : [data.schemes_response];

          const extractedSchemes = schemeArray
            .filter(scheme => scheme && (scheme.Scheme || scheme.scheme_id))
            .map(scheme => ({
              Scheme: scheme.Scheme || '',
              scheme_id: scheme.scheme_id || ''
            }));

          schemesResponseString = JSON.stringify(extractedSchemes);
        } catch (error) {
          console.warn(`Failed to process schemes_response for doc ${doc.id}:`, error);
          schemesResponseString = '[]';
        }
      }

      mergedData.set(doc.id, {
        document_id: doc.id,
        query_text: data.query_text || '',
        query_timestamp: data.query_timestamp || '',
        schemes_response: schemesResponseString,
        session_id: data.session_id || '',
        last_updated: '',  // Will be filled from chatHistory
        messages: ''       // Will be filled from chatHistory
      });
    });

    // Merge chatHistory data
    chatHistorySnapshot.forEach(doc => {
      if (mergedData.has(doc.id)) {
        const data = doc.data();
        const existingData = mergedData.get(doc.id);
        existingData.last_updated = data.last_updated || '';
        existingData.messages = JSON.stringify(data.messages || []);
      }
    });

    // Convert map to array for CSV writing
    const records = Array.from(mergedData.values());

    // Configure CSV Writer
    const csvWriter = createObjectCsvWriter({
      path: path.join(__dirname, 'user-chat-export.csv'),
      header: [
        {id: 'document_id', title: 'Document ID'},
        {id: 'query_text', title: 'query_text'},
        {id: 'query_timestamp', title: 'query_timestamp'},
        {id: 'schemes_response', title: 'schemes_response'},
        {id: 'session_id', title: 'session_id'},
        {id: 'last_updated', title: 'last_updated'},
        {id: 'messages', title: 'messages'}
      ]
    });

    // Write to CSV
    await csvWriter.writeRecords(records);

    console.log('Export completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Export failed:', error);
    process.exit(1);
  }
}

// exportStructure();
exportCollections();
