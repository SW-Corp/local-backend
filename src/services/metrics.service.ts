import {InfluxDB, Point } from '@influxdata/influxdb-client'

class MetricsService {
    private address: string;
    private port: number;
    private org: string;
    private token: string;
    private bucket: string = "YOUR-BUCKET"

    constructor(address: string, port: number, org: string, token: string){
        this.address = address;
        this.port = port;
        this.org = org;
        this.token = token;
    }

    public getMetrics(){
        const client = new InfluxDB({url: `http://${this.address}:${this.port}`, token: token})
        const queryApi = client.getQueryApi(org)

        const query = flux`from(bucket: "${this.bucket}") 
        |> range(start: -1d)
        |> filter(fn: (r) => r._measurement == "weatherstation")`
        queryApi.queryRows(query, {
            next(row, tableMeta) {
                const o = tableMeta.toObject(row)
                console.log(`${o._time} ${o._measurement}: ${o._field}=${o._value}`)
            },
            error(error) {
                console.error(error)
                console.log("FINISHED")
            },
            complete() {
                console.log("Finished ERROR")
            },
        })

    }

    public pushMetrics(){

        const client = new InfluxDB({ url: `http://${this.address}:${this.port}`, token: this.token });
        const writeApi = client.getWriteApi(this.org, this.bucket);
        const point = new Point("weatherstation")
        .tag("location", "San Francisco")
        .floatField("temperature", 23.4)
        .timestamp(new Date());

        writeApi.writePoint(point);

        writeApi
        .close()
        .then(() => {
           console.log("FINISHED")
        })
        .catch((e) => {
            console.error(e);
            console.log("Finished ERROR")
        });
        return "siema"
    }

}

export default MetricsService;
