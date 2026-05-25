### Prerequisites
- Python 3.8+
- Node.js 14+
- npm

### Backend Setup
```bash
cd benchmark
pip install -r requirements.txt
python api.py
```
Backend runs on `http://localhost:5001`

### Frontend Setup
```bash
cd frontend
npm install
npm start
```
Frontend runs on `http://localhost:3000`

### Access the Application
Open your browser and navigate to: **`http://localhost:3000`**

## Usage
1. Enter target URL in the form
2. Configure benchmark parameters (requests, concurrency, rounds)
3. Click **Start Benchmark**
4. Monitor progress in real-time
5. View results and download PDF report

## Latest Release Features
- Real-time progress tracking
- Multi-round performance metrics
- Interactive charts (throughput, response time, status distribution)
- Error analysis
- PDF report export
- Advanced configuration options

