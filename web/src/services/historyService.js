const DATABASE_NAME = "CardioIAHistory";
const STORE_NAME = "exams";
const DATABASE_VERSION = 1;

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);

    request.onupgradeneeded = () => {
      const database = request.result;

      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveExam(exam) {
  const database = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    const record = {
      ...exam,
      id: crypto.randomUUID(),
    };

    transaction.objectStore(STORE_NAME).add(record);

    transaction.oncomplete = () => {
      database.close();
      resolve(record);
    };

    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };

    transaction.onabort = () => {
      database.close();
      reject(transaction.error);
    };
  });
}

export async function getExamHistory() {
  const database = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readonly");
    const request = transaction.objectStore(STORE_NAME).getAll();

    request.onsuccess = () => {
      const records = request.result.sort(
        (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
      );
      resolve(records);
    };

    transaction.oncomplete = () => database.close();

    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
  });
}

export async function deleteExamHistory(id) {
  const database = await openDatabase();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).delete(id);

    transaction.oncomplete = () => {
      database.close();
      resolve();
    };

    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
  });
}
