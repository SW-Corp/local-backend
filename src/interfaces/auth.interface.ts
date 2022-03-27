import { Request } from 'express';

export interface DataStoredInToken {
  email: string;
}

export interface TokenData {
  token: string;
  expiresIn: number;
}

export interface RequestWithUser extends Request {
  user: string;
}
