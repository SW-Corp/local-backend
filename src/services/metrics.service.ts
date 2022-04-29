import {InfluxDB, Point } from '@influxdata/influxdb-client'

class MetricsService {
    private address: string;
    private port: number;
    private org: string;
    private token: string;

    constructor(address: string, port: number, org: string, token: string){
        this.address = address;
        this.port = port;
        this.org = org;
        this.token = token;
    }

    public getMetrics(){

        const client = new InfluxDB({ url: `${this.address}:${this.port}`, token: this.token });
        const writeApi = client.getWriteApi(this.org, "YOUR-BUCKET");
        const point = new Point("weatherstation")
        .tag("location", "San Francisco")
        .floatField("temperature", 23.4)
        .timestamp(new Date());

        writeApi.writePoint(point);

        writeApi
        .close()
        .then(() => {
            return  "FINISHED"
        })
        .catch((e) => {
            console.error(e);
            return "Finished ERROR"
        });
        return "siema"
    }

}

export default MetricsService;
