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

}

export default MetricsService;
