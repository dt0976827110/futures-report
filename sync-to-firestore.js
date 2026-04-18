const admin = require("firebase-admin");
const fs = require("fs");

// 從環境變數讀取 Service Account
const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

async function syncReport() {
  try {
    // 讀取 report.json
    const reportData = JSON.parse(fs.readFileSync("report.json", "utf8"));
    const reportDate = reportData.report_date;

    if (!reportDate) {
      console.error("❌ report.json 缺少 report_date 欄位");
      process.exit(1);
    }

    // 寫入 Firestore /reports/{report_date}
    await db.collection("reports").doc(reportDate).set(reportData);

    console.log(`✅ 日報同步成功：${reportDate}`);
    process.exit(0);
  } catch (error) {
    console.error("❌ 同步失敗：", error);
    process.exit(1);
  }
}

syncReport();
