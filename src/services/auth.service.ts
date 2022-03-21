import { hash, compare } from 'bcrypt';
import { sign } from 'jsonwebtoken';
import { SECRET_KEY } from '@config';
import { CreateUserDto } from '@dtos/users.dto';
import { HttpException } from '@exceptions/HttpException';
import { DataStoredInToken, TokenData } from '@interfaces/auth.interface';
import { User } from '@interfaces/users.interface';
import userModel from '@models/users.model';
import { isEmpty } from '@utils/util';
import fetch from 'node-fetch';

class AuthService{
  public users = userModel;
  private authAddr: string;
  private authPort: number;
  constructor(authAddr: string, authPort: number){
    this.authAddr = authAddr;
    this.authPort = authPort;
  }

  public async signup(userData: CreateUserDto): Promise<User> {
    if (isEmpty(userData)) throw new HttpException(400, "You're not userData");

    const findUser: User = this.users.find(user => user.email === userData.email);
    if (findUser) throw new HttpException(409, `You're email ${userData.email} already exists`);

    const hashedPassword = await hash(userData.password, 10);
    const createUserData: User = { id: this.users.length + 1, ...userData, password: hashedPassword };

    return createUserData;
  }

  public async login(userData: CreateUserDto): Promise<{ cookie: string; email: string }> {
    if (isEmpty(userData)) throw new HttpException(400, "You're not userData");
    
    const body = {"username": userData.email, "password": userData.password}
    console.log(body)
    let response;
    try{
      response = await fetch(`http://${this.authAddr}:${this.authPort}/login`, {method: 'POST', body: JSON.stringify(body)});
    }
    catch{
      throw new HttpException(500, `Cant connect to authenticator`);
    }
    

    if (response.status == 401){
      throw new HttpException(401, `Wrong email or password`);
    }
    else if (!response.ok){
      throw new HttpException(response.status, response.text());
    }
    else{
      const email: string = userData.email
      const tokenData = this.createToken(userData.email);
      const cookie = this.createCookie(tokenData);
  
      return { cookie, email};
    }

  }

  // public async logout(userData: string): Promise<User> {
  //   if (isEmpty(userData)) throw new HttpException(400, "You're not userData");

  //   const findUser: User = this.users.find(user => user.email === userData.email && user.password === userData.password);
  //   if (!findUser) throw new HttpException(409, "You're not user");

  //   return findUser;
  // }

  public createToken(user: string): TokenData {
    const dataStoredInToken: DataStoredInToken = { email:  user};
    const secretKey: string = SECRET_KEY;
    const expiresIn: number = 60 * 60;

    return { expiresIn, token: sign(dataStoredInToken, secretKey, { expiresIn }) };
  }

  public createCookie(tokenData: TokenData): string {
    return `Authorization=${tokenData.token}; HttpOnly; Max-Age=${tokenData.expiresIn};`;
  }
}

export default AuthService;
