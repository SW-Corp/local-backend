import App from '@/app';
import AuthRoute from '@routes/auth.route';
import IndexRoute from '@routes/index.route';
import WorkstationRoute from '@routes/workstation.route';
import validateEnv from '@utils/validateEnv';

validateEnv();

const app = new App([new IndexRoute(), new AuthRoute(), new WorkstationRoute()]);

app.listen();
