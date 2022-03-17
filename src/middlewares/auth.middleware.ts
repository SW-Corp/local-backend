import { NextFunction, Response } from 'express';
import { verify } from 'jsonwebtoken';
import { SECRET_KEY, AUTH_ADDR, AUTH_PORT } from '@config';
import { HttpException } from '@exceptions/HttpException';
import { DataStoredInToken, RequestWithUser } from '@interfaces/auth.interface';
import userModel from '@models/users.model';
import fetch from 'node-fetch';


const authMiddleware = async (req: RequestWithUser, res: Response, next: NextFunction) => {
  try {
    const Authorization = req.cookies['Authorization'] || (req.header('Authorization') ? req.header('Authorization').split('Bearer ')[1] : null);

    if (Authorization) {
      const secretKey: string = SECRET_KEY;
      const verificationResponse = (await verify(Authorization, secretKey)) as DataStoredInToken;
      console.log(verificationResponse)
      const userEmail = verificationResponse.email;
      // const findUser = userModel.find(user => user.id === userId);
      const body = {"username": userEmail}
      const response = await fetch(`http://${AUTH_ADDR}:${AUTH_PORT}/usr`, {method: 'POST', body: JSON.stringify(body)});
      if (response.status == 200) {
        // req.user = findUser;
        next();
      } else {
        next(new HttpException(401, 'Wrong authentication token'));
      }
    } else {
      next(new HttpException(404, 'Authentication token missing'));
    }
  } catch (error) {
    next(new HttpException(401, 'Wrong authentication token'));
  }
};

export default authMiddleware;
